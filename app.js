/* =========================================================
   Plancito · lógica de la página
   Lee data/eventos.json (scraper) y data/lugares.json (lista propia + tours)
   ========================================================= */
(function () {
  'use strict';

  const PERSONAS = 2;
  const PRESUPUESTOS = [0, 50, 100, 150, 250];

  const TIPOS = [
    ['todo', '¡Me apunto a todo!'], ['restaurantes', 'Restaurantes'], ['cafe', 'Café'],
    ['bar', 'Bar'], ['cine', 'Cine'], ['cultural', 'Cultural'], ['aire', 'Aire libre']
  ];
  const TIPOS_REALES = TIPOS.slice(1).map((t) => t[0]);

  const ICONO_TIPO = {
    todo: '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2l2.2 6.3 6.3 2.2-6.3 2.2L12 19l-2.2-6.3-6.3-2.2 6.3-2.2z"/><path d="M19 15l.9 2.1 2.1.9-2.1.9L19 21l-.9-2.1-2.1-.9 2.1-.9z"/></svg>',
    restaurantes: linea('<path d="M8 3v18M5 3v6a3 3 0 0 0 6 0V3"/><path d="M17 21V3c-2 1-3 4-3 7h3"/>'),
    cafe: linea('<path d="M4 9h12v5a5 5 0 0 1-5 5H9a5 5 0 0 1-5-5z"/><path d="M16 11h2a2 2 0 0 1 0 4h-2"/><path d="M8 3v3M12 3v3"/>'),
    bar: linea('<path d="M5 4h14l-7 8z"/><path d="M12 12v8M8 20h8"/>'),
    cine: linea('<rect x="3" y="8" width="18" height="12" rx="2"/><path d="M3 8l3-5h4l-3 5M10 8l3-5h4l-3 5"/>'),
    cultural: linea('<path d="M3 10l9-6 9 6"/><path d="M5 10v8M10 10v8M14 10v8M19 10v8M3 20h18"/>'),
    aire: linea('<path d="M12 3l6 9h-4l4 6H6l4-6H6z"/><path d="M12 18v4"/>')
  };

  const ATRIBUTOS = {
    gratis: ['Gratis', '#FFF1B8', '#5C4300', '<path d="M3 12V4h8l10 10-8 8z"/><circle cx="7.5" cy="8.5" r="1.5"/>'],
    pet: ['Pet friendly', '#FFE7D6', '#8A3200', '<circle cx="6" cy="10" r="2"/><circle cx="10" cy="6" r="2"/><circle cx="14" cy="6" r="2"/><circle cx="18" cy="10" r="2"/><path d="M8 18c0-3 2-5 4-5s4 2 4 5c0 2-8 2-8 0z"/>'],
    ninos: ['Para niños', '#FFE1EC', '#9D174D', '<ellipse cx="12" cy="9" rx="5" ry="6"/><path d="M12 15c0 2-2 3 0 6"/>'],
    terraza: ['Terraza', '#DCEBFF', '#0B3D91', '<path d="M3 11a9 7 0 0 1 18 0z"/><path d="M12 11v10M8 21h8"/>'],
    vista: ['Vista al mar', '#D7F5FF', '#0B4A6F', '<path d="M2 12c3-3 5-3 8 0s5 3 8 0 4-2 4-2M2 18c3-3 5-3 8 0s5 3 8 0 4-2 4-2"/><circle cx="17" cy="5" r="2"/>'],
    vegetariano: ['Opción vegetariana', '#DDF3E4', '#0B5A2A', '<path d="M5 20c0-9 6-15 15-15 0 9-6 15-15 15z"/><path d="M5 20l8-8"/>'],
    postres: ['Postres', '#FFE1EC', '#9D174D', '<path d="M8 12l4 10 4-10"/><circle cx="12" cy="8" r="4"/>'],
    wifi: ['Wifi para trabajar', '#EEEAF7', '#3B2D7A', '<path d="M2 9a15 15 0 0 1 20 0M5 13a10 10 0 0 1 14 0M8.5 16.5a5 5 0 0 1 7 0"/><circle cx="12" cy="20" r="1"/>'],
    musica: ['Música en vivo', '#F1E2FF', '#5B1A99', '<path d="M9 18V5l11-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="17" cy="16" r="3"/>'],
    happy: ['Happy hour', '#FFF1B8', '#5C4300', '<path d="M5 4h14l-7 8z"/><path d="M12 12v8M8 20h8"/>'],
    romantico: ['Romántico', '#FFE1EC', '#9D174D', '<path d="M12 20s-7-4.5-9-9a4.5 4.5 0 0 1 9-3 4.5 4.5 0 0 1 9 3c-2 4.5-9 9-9 9z"/>'],
    '3d': ['Sala 3D', '#FFE1E1', '#8F1D1D', '<circle cx="7" cy="14" r="3"/><circle cx="17" cy="14" r="3"/><path d="M10 14h4M4 14V8h16v6"/>']
  };
  const ATRIBUTOS_POR_TIPO = {
    todo: ['gratis', 'pet', 'ninos', 'terraza'],
    restaurantes: ['romantico', 'pet', 'terraza', 'vista', 'vegetariano', 'ninos'],
    cafe: ['pet', 'postres', 'wifi', 'terraza'],
    bar: ['romantico', 'musica', 'happy', 'terraza', 'pet'],
    cine: ['3d', 'ninos', 'gratis'],
    cultural: ['gratis', 'ninos'],
    aire: ['gratis', 'ninos', 'pet']
  };

  const COLOR_CATEGORIA = {
    'Fútbol': ['#DDF3E4', '#0B5A2A'], 'Deporte': ['#DCEBFF', '#0B3D91'], 'Paseo': ['#DDF3E4', '#0B5A2A'],
    'Concierto': ['#F1E2FF', '#5B1A99'], 'Festival': ['#FFE1EC', '#9D174D'], 'Fiesta': ['#F1E2FF', '#5B1A99'],
    'Teatro': ['#FFE1E1', '#8F1D1D'], 'Stand up': ['#FFF1B8', '#5C4300'], 'Cine': ['#FFE1E1', '#8F1D1D'],
    'Comida': ['#FFE7D6', '#8A3200'], 'Restaurante': ['#FFE7D6', '#8A3200'], 'Café': ['#F3E5D8', '#6B3A12'],
    'Bar': ['#F1E2FF', '#5B1A99'], 'Cultura': ['#E0F2FE', '#0B4A6F'], 'Aire libre': ['#DDF3E4', '#0B5A2A'],
    'Show': ['#FFF1B8', '#5C4300'], 'Familia': ['#FFE1EC', '#9D174D'],
    'Full day': ['#DDF3E4', '#0B5A2A'], 'Tour': ['#E0F2FE', '#0B4A6F'], 'Free tour': ['#FFF1B8', '#5C4300'],
    'Exposición': ['#E0F2FE', '#0B4A6F'], 'Charla': ['#EEEAF7', '#3B2D7A'], 'Taller': ['#FFE7D6', '#8A3200'],
    'Feria': ['#FFE1EC', '#9D174D'], 'Danza': ['#F1E2FF', '#5B1A99'], 'Pádel': ['#DCEBFF', '#0B3D91']
  };

  // ---------- Ilustraciones (si la foto no carga) ----------
  const ILUS = {
    futbol: '<rect width="300" height="160" fill="#16A34A"/><g fill="#22B357"><rect x="0" width="40" height="160"/><rect x="80" width="40" height="160"/><rect x="160" width="40" height="160"/><rect x="240" width="40" height="160"/></g><g stroke="#fff" stroke-width="3" fill="none" opacity=".85"><rect x="12" y="12" width="276" height="136"/><line x1="150" y1="12" x2="150" y2="148"/><circle cx="150" cy="80" r="30"/></g><circle cx="208" cy="108" r="24" fill="#fff" stroke="#1B1036" stroke-width="3"/><path d="M208 95l11 8-4 13h-14l-4-13z" fill="#1B1036"/>',
    concierto: '<rect width="300" height="160" fill="#2A1059"/><polygon points="55,0 85,0 160,160 -10,160" fill="#FFC933" opacity=".38"/><polygon points="215,0 245,0 310,160 140,160" fill="#FF4F3A" opacity=".38"/><polygon points="140,0 160,0 210,160 90,160" fill="#3DB7FF" opacity=".25"/><g fill="#12062E"><rect y="138" width="300" height="22"/><circle cx="20" cy="136" r="15"/><circle cx="52" cy="132" r="14"/><circle cx="86" cy="138" r="16"/><circle cx="120" cy="130" r="14"/><circle cx="154" cy="136" r="15"/><circle cx="188" cy="131" r="14"/><circle cx="222" cy="137" r="16"/><circle cx="256" cy="132" r="14"/><circle cx="288" cy="136" r="15"/></g>',
    comida: '<rect width="300" height="160" fill="#FF7A45"/><circle cx="250" cy="34" r="20" fill="#FFC933"/><path d="M95 128q10-30 22-8q6-24 18-4q8-28 20 0q10-26 22-2q8-22 20 6z" fill="#FFC933"/><rect x="70" y="92" width="160" height="10" rx="5" fill="#1B1036"/><ellipse cx="115" cy="84" rx="30" ry="11" fill="#7A2E0E"/><ellipse cx="185" cy="84" rx="28" ry="10" fill="#8A3A12"/>',
    deporte: '<rect width="300" height="160" fill="#2563EB"/><path d="M-20 170Q150 30 320 170" fill="#E4572E"/><g stroke="#fff" stroke-width="3" fill="none"><path d="M10 170Q150 62 290 170"/><path d="M40 170Q150 92 260 170"/></g><circle cx="150" cy="58" r="20" fill="#FFC933" stroke="#1B1036" stroke-width="3"/>',
    gratis: '<rect width="300" height="160" fill="#FFC933"/><g transform="rotate(-8 150 80)"><path d="M70 45h160a12 12 0 0 0 0 24v22a12 12 0 0 0 0 24H70a12 12 0 0 0 0-24V69a12 12 0 0 0 0-24z" fill="#1B1036"/><text x="140" y="89" text-anchor="middle" font-family="Arial,sans-serif" font-weight="800" font-size="30" fill="#fff">GRATIS</text></g>',
    teatro: '<rect width="300" height="160" fill="#2A0A12"/><ellipse cx="150" cy="150" rx="90" ry="22" fill="#FFC933" opacity=".45"/><path d="M0 0h110q-20 40-10 80t-30 80H0z" fill="#B91C1C"/><path d="M300 0H190q20 40 10 80t30 80h70z" fill="#B91C1C"/><rect width="300" height="16" fill="#7F1D1D"/><circle cx="150" cy="92" r="22" fill="#FFF1B8"/>'
  };
  const ILUS_POR_CATEGORIA = {
    'Fútbol': 'futbol', 'Deporte': 'deporte', 'Paseo': 'deporte', 'Aire libre': 'deporte', 'Full day': 'deporte', 'Pádel': 'deporte',
    'Concierto': 'concierto', 'Festival': 'concierto', 'Fiesta': 'concierto', 'Bar': 'concierto',
    'Comida': 'comida', 'Restaurante': 'comida', 'Café': 'comida'
  };

  // ---------- Estado ----------
  const E = {
    fecha: 'finde', presupuesto: 150, tipos: new Set(), estrellas: 0, attrs: new Set(),
    romantico: false, q: '', heroIdx: 0, masFiltros: false, calAbierto: false
  };
  let PLANES = [];
  let ACTUALIZADO = '';

  // ---------- Utilidades ----------
  function linea(paths) {
    return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + paths + '</svg>';
  }
  const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const soles = (v) => v === 0 ? 'Gratis' : 'S/ ' + (Math.round(v) === v ? v : v.toFixed(2));
  const $ = (id) => document.getElementById(id);

  const fmtISO = new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Lima' });
  const hoy = () => fmtISO.format(new Date());
  function sumarDias(iso, n) {
    const d = new Date(iso + 'T12:00:00Z');
    d.setUTCDate(d.getUTCDate() + n);
    return d.toISOString().slice(0, 10);
  }
  const diaSemana = (iso) => new Date(iso + 'T12:00:00Z').getUTCDay(); // 0 domingo
  const DIAS_CORTO = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];
  const DIAS_LARGO = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado'];
  const MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'setiembre', 'octubre', 'noviembre', 'diciembre'];
  const MESES_CORTO = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'set', 'oct', 'nov', 'dic'];
  const numDia = (iso) => +iso.slice(8, 10);
  const mesDe = (iso) => +iso.slice(5, 7) - 1;
  const fechaCorta = (iso) => DIAS_CORTO[diaSemana(iso)] + ' ' + numDia(iso) + ' ' + MESES_CORTO[mesDe(iso)];
  const fechaLarga = (iso) => DIAS_LARGO[diaSemana(iso)] + ' ' + numDia(iso) + ' de ' + MESES[mesDe(iso)];

  function diasDelFinde() {
    const h = hoy();
    const ds = diaSemana(h);
    if (ds === 0) return [h];
    if (ds === 6) return [h, sumarDias(h, 1)];
    if (ds === 5) return [h, sumarDias(h, 1), sumarDias(h, 2)];
    const viernes = sumarDias(h, 5 - ds);
    return [viernes, sumarDias(viernes, 1), sumarDias(viernes, 2)];
  }
  function diasElegidos() {
    const h = hoy();
    if (E.fecha === 'hoy') return [h];
    if (E.fecha === 'finde') return diasDelFinde();
    if (E.fecha === 'semana') return Array.from({ length: 7 }, (_, i) => sumarDias(h, i));
    return [E.fecha];
  }
  function textoFecha() {
    if (E.fecha === 'hoy') return 'Hoy, ' + fechaLarga(hoy());
    if (E.fecha === 'finde') {
      const d = diasDelFinde();
      return d.length === 1 ? 'Este finde (' + fechaCorta(d[0]) + ')' : 'Este finde (' + fechaCorta(d[0]) + ' al ' + fechaCorta(d[d.length - 1]) + ')';
    }
    if (E.fecha === 'semana') return 'Los próximos 7 días';
    return fechaLarga(E.fecha);
  }

  // ---------- Datos ----------
  function cargar() {
    const ev = fetch('data/eventos.json', { cache: 'no-cache' }).then((r) => r.json()).catch(() => ({ eventos: [] }));
    const lu = fetch('data/lugares.json', { cache: 'no-cache' }).then((r) => r.json()).catch(() => ({ lugares: [] }));
    const lista = (u) => fetch(u, { cache: 'no-cache' }).then((r) => r.json()).then((d) => Array.isArray(d) ? d : []).catch(() => []);
    // data/manual/*.json: lo que agregas tú desde admin.html (aparece al toque, sin esperar al scraper)
    Promise.all([ev, lu, lista('data/manual/eventos.json'), lista('data/manual/lugares.json')]).then(([eventos, lugares, evManual, luManual]) => {
      ACTUALIZADO = eventos.actualizado || '';
      const hoyISO = hoy();
      const propios = evManual.filter((e) => e.nombre && e.inicio && (e.fin || e.inicio) >= hoyISO).map((e) => Object.assign({ fuente: 'Plancito' }, e));
      PLANES = (eventos.eventos || []).concat(propios).map((e, i) => ({
        id: 'e' + i, nombre: e.nombre, inicio: e.inicio, fin: e.fin || e.inicio, hora: e.hora, lugar: e.lugar,
        categoria: e.categoria, tipo: e.tipo, precio: e.precio, imagen: e.imagen_local || e.imagen, url: e.url, fuente: e.fuente, destacado: !!e.destacado,
        atributos: [], siempre: false, ejemplo: false, calificacion: 0
      })).concat(luManual.concat(lugares.lugares || []).map((l, i) => ({
        id: 'l' + i, nombre: l.nombre, lugar: l.lugar, categoria: l.categoria, tipo: l.tipo, precio: l.precio,
        calificacion: l.calificacion || 0, atributos: l.atributos || [], url: l.url, imagen: l.imagen_local || l.imagen || '',
        salidas: l.salidas || '', resenas: l.resenas || 0, destacado: !!l.destacado, fotoAutor: l.foto_autor || '', fuente: l.ejemplo ? 'Ejemplo' : (l.fuente || 'Plancito'), siempre: true, ejemplo: !!l.ejemplo
      }))).filter((p) => typeof p.precio === 'number' && p.nombre);
      PLANES.forEach((p) => { if (p.precio === 0 && !p.atributos.includes('gratis')) p.atributos.push('gratis'); });
      render();
      if (location.hash === '#para-una-cita') abrirCita();
    });
  }

  const ocurre = (p, dias) => p.siempre || dias.some((d) => p.inicio <= d && d <= p.fin);
  const total = (p) => p.precio * PERSONAS;

  function tiposActivos(dias, tope) {
    const n = {};
    TIPOS_REALES.forEach((t) => { n[t] = 0; });
    PLANES.forEach((p) => { if (n[p.tipo] !== undefined && ocurre(p, dias) && total(p) <= tope) n[p.tipo]++; });
    return n;
  }

  // ---------- Portadas (foto o ilustración) ----------
  function ilustracion(p) {
    const k = p.precio === 0 && !ILUS_POR_CATEGORIA[p.categoria] ? 'gratis' : (ILUS_POR_CATEGORIA[p.categoria] || 'teatro');
    return '<svg viewBox="0 0 300 160" preserveAspectRatio="xMidYMid slice" aria-hidden="true">' + ILUS[k] + '</svg>';
  }
  function portada(p) {
    if (p.imagen) {
      return '<div class="portada-plan"><img src="' + esc(p.imagen) + '" alt="" loading="lazy" referrerpolicy="no-referrer" data-ilus="' + esc(p.id) + '"></div>';
    }
    return '<div class="portada-plan">' + ilustracion(p) + '</div>';
  }
  document.addEventListener('error', (ev) => {
    const img = ev.target;
    if (img.tagName === 'IMG' && img.dataset.ilus) {
      const p = PLANES.find((x) => x.id === img.dataset.ilus);
      if (p) img.outerHTML = ilustracion(p);
    }
  }, true);

  function frase(p) {
    const t = total(p);
    const sobra = E.presupuesto - t;
    if (t === 0) return ['Gratis, gratis. Solo lleven ganas.', 'gratis'];
    if (sobra >= 30) return ['Les sobran S/ ' + Math.floor(sobra) + ': alcanza para unos picarones', 'sobra'];
    if (sobra >= 10) return ['Les sobran S/ ' + Math.floor(sobra) + ' para un heladito', 'sobra'];
    if (p.calificacion >= 4.7) return ['Top: de los mejor calificados', 'justo'];
    return ['Justo para su presupuesto', 'justo'];
  }
  const cuando = (p) => p.siempre ? (p.salidas ? 'Salidas: ' + p.salidas : 'Toda la semana') : (p.inicio === p.fin ? fechaCorta(p.inicio) : 'Hasta el ' + fechaCorta(p.fin)) + (p.hora && !p.siempre ? ' · ' + p.hora : '');
  const textoBoton = (p) => p.ejemplo ? 'Lugar de ejemplo' : (p.siempre ? (p.fuente && p.fuente !== 'Plancito' ? 'Ver en ' + p.fuente : 'Ver ubicación') : 'Ver y comprar en ' + p.fuente);
  const enlace = (p) => p.url ? ' href="' + esc(p.url) + '" target="_blank" rel="noopener sponsored"' : ' href="#" aria-disabled="true" data-accion="nada"';


  // ---------- Búsqueda por texto ----------
  const normal = (s) => String(s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const NOMBRE_TIPO = Object.fromEntries(TIPOS);
  function coincide(p, palabras) {
    if (!palabras.length) return true;
    const texto = normal([p.nombre, p.lugar, p.categoria, NOMBRE_TIPO[p.tipo], p.fuente, p.precio === 0 ? 'gratis free' : '', p.atributos.includes('romantico') ? 'cena romantica cita pareja' : '',
      (p.atributos || []).map((a) => ATRIBUTOS[a] ? ATRIBUTOS[a][0] : '').join(' ')].join(' '));
    return palabras.every((w) => texto.includes(w));
  }
  const palabrasDe = (q) => normal(q).split(/\s+/).filter(Boolean);

  // ---------- Filtros ----------
  function calcular(tope, sinExtras) {
    if (tope === undefined) tope = E.presupuesto;
    const dias = diasElegidos();
    const disponibles = tiposActivos(dias, tope);
    const sel = TIPOS_REALES.filter((t) => E.tipos.has(t) && disponibles[t] > 0);
    const todo = sel.length === 0;
    const attrsVisibles = todo ? ATRIBUTOS_POR_TIPO.todo
      : sel.reduce((acc, t) => acc.concat(ATRIBUTOS_POR_TIPO[t].filter((a) => !acc.includes(a))), []);
    const attrsActivos = [...E.attrs].filter((a) => attrsVisibles.includes(a));
    const esRomantico = (p) => p.atributos.includes('romantico');
    const romanticos = PLANES.filter((p) => ocurre(p, dias) && total(p) <= tope && esRomantico(p)).length;
    const planes = PLANES.filter((p) => ocurre(p, dias) && total(p) <= tope
      && (todo || sel.includes(p.tipo))
      && (!E.romantico || esRomantico(p))
      && (!E.estrellas || p.calificacion >= E.estrellas)
      && attrsActivos.every((a) => p.atributos.includes(a)))
      .sort((a, b) => total(b) - total(a) || a.nombre.localeCompare(b.nombre));
    // numerito de "Planes gratis": cuántos verían con sus filtros actuales
    const gratis = sinExtras ? 0 : (tope === 0 ? planes.length : calcular(0, true).planes.length);
    const palabras = palabrasDe(E.q);
    const encontrados = planes.filter((p) => coincide(p, palabras));
    return { dias, disponibles, romanticos, gratis, sel, todo, attrsVisibles, attrsActivos, planes, palabras, encontrados };
  }

  // ---------- Render: plan destacado (hero) ----------
  function destacados(c) {
    const eventos = c.planes.filter((p) => !p.siempre);
    const lugares = c.planes.filter((p) => p.siempre).sort((a, b) => b.calificacion - a.calificacion);
    return eventos.concat(lugares).slice(0, 5);
  }

  function renderHero(c) {
    const hero = $('hero');
    const lista = destacados(c);
    hero.classList.toggle('oculto', c.palabras.length > 0);
    if (!lista.length) {
      hero.innerHTML = '<div class="hero-vacio"><span class="eyebrow">Lima · ' + esc(textoFecha()) + '</span>' +
        '<h1>' + tituloPresupuesto() + '</h1><p>No hay planes con estos filtros. Prueba otra fecha o sube un poco el monto.</p></div>';
      return;
    }
    if (E.heroIdx >= lista.length) E.heroIdx = 0;
    const p = lista[E.heroIdx];
    const f = frase(p);
    const puntos = lista.length > 1 ? '<div class="hero-puntos" role="tablist" aria-label="Planes destacados">' + lista.map((x, i) =>
      '<button type="button" role="tab" aria-selected="' + (i === E.heroIdx) + '" aria-label="' + esc(x.nombre) + '" data-accion="hero" data-valor="' + i + '"></button>').join('') + '</div>' : '';
    hero.innerHTML =
      '<div class="hero-fondo">' + portada(p) + '</div><div class="hero-velo"></div>' +
      '<div class="hero-texto">' +
      '<span class="eyebrow">' + tituloPresupuesto() + '</span>' +
      '<span class="hero-sello">★ Plan destacado · ' + esc(p.categoria || '') + '</span>' +
      '<h1>' + esc(p.nombre) + '</h1>' +
      '<span class="hero-meta"><b>' + soles(total(p)) + (total(p) ? ' para dos' : '') + '</b> · ' + esc(cuando(p)) + (p.lugar ? ' · ' + esc(p.lugar) : '') + '</span>' +
      '<p class="hero-frase">' + esc(f[0]) + '</p>' +
      '<div class="hero-botones"><a class="btn-play"' + enlace(p) + '>' + linea('<path d="M7 17L17 7M8 7h9v9"/>') + esc(textoBoton(p)) + '</a>' +
      '<a class="btn-gris" href="' + compartir(p) + '" target="_blank" rel="noopener">' + linea('<path d="M4 12v7a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-7M16 6l-4-4-4 4M12 2v13"/>') + 'Compartir</a></div>' +
      '<button type="button" class="hero-ruleta" data-accion="abrir-ruleta">' + linea('<rect x="3" y="3" width="18" height="18" rx="4"/><circle cx="8.5" cy="8.5" r="1.3" fill="currentColor"/><circle cx="15.5" cy="15.5" r="1.3" fill="currentColor"/><circle cx="12" cy="12" r="1.3" fill="currentColor"/>') + '<span>¿No se deciden? <b>Que decida la ruleta</b></span></button>' +
      puntos + '</div>';
  }
  const tituloPresupuesto = () => E.presupuesto === 0 ? '¿Qué hacemos <span class="acento">gratis</span>?' : '¿Qué hacemos con <span class="acento">S/ ' + E.presupuesto + '</span>?';
  function compartir(p) {
    const txt = '¿Vamos a "' + p.nombre + '"? Lo vi en Plancito. ' + cuando(p) + ' · ' + soles(total(p)) + ' para dos. ' + (p.url || location.href);
    return 'https://wa.me/?text=' + encodeURIComponent(txt);
  }

  // ---------- Render: barra de filtros ----------
  function renderFiltros(c) {
    const h = hoy();
    const conPlanes = new Set();
    for (let i = 0; i < 14; i++) {
      const d = sumarDias(h, i);
      if (PLANES.some((p) => !p.siempre && ocurre(p, [d]) && total(p) <= E.presupuesto)) conPlanes.add(d);
    }
    const incluidos = new Set(c.dias);
    let dias = '';
    for (let i = 0; i < 14; i++) {
      const d = sumarDias(h, i);
      const clases = ['dia', incluidos.has(d) ? 'incluido' : '', conPlanes.has(d) ? 'con-planes' : ''].join(' ');
      dias += '<button type="button" role="option" class="' + clases + '" aria-selected="' + (E.fecha === d) + '" data-accion="fecha" data-valor="' + d + '"><small>' + (i === 0 ? 'Hoy' : DIAS_CORTO[diaSemana(d)]) + '</small><b>' + numDia(d) + '</b></button>';
    }
    const atajo = (v, t) => '<button type="button" class="chip" aria-pressed="' + (E.fecha === v) + '" data-accion="fecha" data-valor="' + v + '">' + t + '</button>';
    const presupuesto = PRESUPUESTOS.map((v) => v === 0
      ? '<button type="button" class="chip chip-gratis" aria-pressed="' + (E.presupuesto === 0) + '" data-accion="presupuesto" data-valor="0">' + linea(ATRIBUTOS.gratis[3]) + 'Planes gratis' + (c.gratis ? ' <em>' + c.gratis + '</em>' : '') + '</button>'
      : '<button type="button" class="chip" aria-pressed="' + (E.presupuesto === v) + '" data-accion="presupuesto" data-valor="' + v + '">S/ ' + v + '</button>').join('')
      + '<button type="button" class="chip chip-cita" data-accion="cita">' + linea('<path d="M12 20s-7-4.5-9-9a4.5 4.5 0 0 1 9-3 4.5 4.5 0 0 1 9 3c-2 4.5-9 9-9 9z"/>') + 'Para una cita</button>';
    const tipos = TIPOS.map(([k, t]) => {
      const on = k === 'todo' ? c.todo && !E.romantico : c.sel.includes(k);
      const off = k !== 'todo' && c.disponibles[k] === 0;
      const boton = '<button type="button" class="chip" aria-pressed="' + on + '"' + (off ? ' disabled title="No hay planes de este tipo con ese presupuesto y fecha"' : '') + ' data-accion="tipo" data-valor="' + k + '">' + ICONO_TIPO[k] + (k === 'todo' ? 'Todo' : t) + '</button>';
      return k !== 'todo' ? boton : boton +
        '<button type="button" class="chip chip-romantico" aria-pressed="' + E.romantico + '"' + (c.romanticos ? '' : ' disabled title="No hay cenas románticas con ese presupuesto y fecha"') + ' data-accion="romantico">' + linea('<path d="M12 20s-7-4.5-9-9a4.5 4.5 0 0 1 9-3 4.5 4.5 0 0 1 9 3c-2 4.5-9 9-9 9z"/>') + 'Cena romántica</button>';
    }).join('');
    const estrellasChips = [[0, 'Cualquiera'], [3, '3+ ★'], [4, '4+ ★'], [4.5, '4.5+ ★']].map(([v, t]) =>
      '<button type="button" class="chip" aria-pressed="' + (E.estrellas === v) + '" data-accion="estrellas" data-valor="' + v + '">' + t + '</button>').join('');
    const attrChips = c.attrsVisibles.map((a) => {
      const [t, claro, fuerte, icono] = ATRIBUTOS[a];
      const on = E.attrs.has(a);
      const estilo = on ? 'background:' + claro + ';color:' + fuerte + ';border-color:' + claro : '';
      return '<button type="button" class="chip" style="' + estilo + '" aria-pressed="' + on + '" data-accion="attr" data-valor="' + a + '">' + linea(icono) + t + '</button>';
    }).join('');
    const extras = (E.estrellas ? 1 : 0) + c.attrsActivos.length;

    $('filtros').innerHTML =
      '<div class="filtros-fila">' +
      '<div class="fecha-caja"><button type="button" class="fecha-boton" aria-haspopup="listbox" aria-expanded="' + E.calAbierto + '" data-accion="calendario">' +
      linea('<rect x="3" y="5" width="18" height="16" rx="3"/><path d="M3 10h18M8 3v4M16 3v4"/>') + '<span>' + esc(textoFecha()) + '</span>' +
      linea('<polyline points="6 9 12 15 18 9"/>').replace('<svg', '<svg class="flecha"') + '</button>' +
      (E.calAbierto ? '<div class="calendario" role="listbox" aria-label="Elegir fecha"><div class="atajos">' + atajo('hoy', 'Hoy') + atajo('finde', 'Este finde') + atajo('semana', '7 días') + '</div>' +
        '<span class="mes">Próximos 14 días · el punto rojo indica que hay eventos</span><div class="dias">' + dias + '</div></div>' : '') +
      '</div>' +
      '<div class="grupo-chips" role="group" aria-label="Presupuesto para dos personas"><span class="mini-etiqueta">Para 2</span>' + presupuesto + '</div>' +
      '<button type="button" class="chip chip-mas" aria-expanded="' + E.masFiltros + '" data-accion="mas-filtros">' + linea('<path d="M4 6h16M7 12h10M10 18h4"/>') + 'Más filtros' + (extras ? ' <em>' + extras + '</em>' : '') + '</button>' +
      '</div>' +
      '<div class="filtros-fila tipos" role="group" aria-label="Tipo de plan">' + tipos + '</div>' +
      (E.masFiltros ? '<div class="filtros-mas"><div class="linea"><span>Calificación</span>' + estrellasChips + '</div>' +
        '<div class="linea"><span>Que tenga</span>' + attrChips + '</div>' +
        '<small>Las estrellas aplican a locales (cafés, bares, restaurantes).</small></div>' : '');
  }

  // ---------- Render: tarjetas y filas ----------
  function tarjeta(p) {
    const col = COLOR_CATEGORIA[p.categoria] || ['#EEEAF7', '#3B2D7A'];
    const f = frase(p);
    return '<article class="tarjeta"><a class="tarjeta-link"' + enlace(p) + ' aria-label="' + esc(p.nombre + ' · ' + textoBoton(p)) + '"></a>' +
      '<div class="foto">' + portada(p) +
      '<span class="cat" style="background:' + col[0] + ';color:' + col[1] + '">' + esc(p.categoria) + '</span>' +
      '<span class="sticker">' + soles(total(p)) + '</span></div><div class="cuerpo">' +
      '<h4>' + esc(p.nombre) + '</h4>' +
      '<span class="cuando">' + esc(cuando(p)) + (p.lugar ? ' · ' + esc(p.lugar) : '') + '</span>' +
      (p.calificacion ? '<span class="estrellas"><b>★ ' + p.calificacion.toFixed(1) + '</b>' + (p.resenas ? ' <small>(' + p.resenas.toLocaleString('es-PE') + ' reseñas en Google)</small>' : '') + (p.ejemplo ? '<span class="etiqueta-ejemplo">EJEMPLO</span>' : '') + '</span>' : '') +
      '<span class="gracia ' + f[1] + '">' + esc(f[0]) + '</span>' +
      '<span class="ir">' + esc(textoBoton(p)) + ' →</span>' + (p.fotoAutor ? '<small class="credito">Foto: ' + esc(p.fotoAutor) + ' · Google Maps</small>' : '') + '</div></article>';
  }

  const GRUPOS = [
    ['Para una cena romántica', (p) => p.atributos.includes('romantico')],
    ['Si quieren gritar y saltar', (p) => ['Concierto', 'Festival', 'Fiesta', 'Fútbol', 'Deporte'].includes(p.categoria)],
    ['Full days para escaparse de Lima', (p) => p.categoria === 'Full day'],
    ['Para comer rico', (p) => p.tipo === 'restaurantes' || p.tipo === 'cafe'],
    ['Para una cita tranqui', (p) => p.tipo === 'bar' || p.tipo === 'cine' || ['Teatro', 'Stand up'].includes(p.categoria)],
    ['Gratis y al aire libre', (p) => p.tipo === 'aire' || p.precio === 0],
    ['Para alimentar el alma', (p) => p.tipo === 'cultural'],
    ['Y algo más', () => true]
  ];

  function fila(id, titulo, items, extra) {
    return '<section class="fila" aria-label="' + esc(titulo) + '"><div class="fila-titulo"><h2>' + titulo + '</h2>' + (extra || '<span>' + items.length + '</span>') + '</div>' +
      '<div class="fila-riel"><button type="button" class="flecha-fila izq" aria-label="Anteriores" data-accion="mover" data-valor="' + id + '" data-dir="-1">‹</button>' +
      '<div class="carrusel" id="' + id + '">' + items.map(tarjeta).join('') + '</div>' +
      '<button type="button" class="flecha-fila der" aria-label="Siguientes" data-accion="mover" data-valor="' + id + '" data-dir="1">›</button></div></section>';
  }

  function renderFilas(c) {
    let html = '';
    if (c.palabras.length) {
      const n = c.encontrados.length;
      html += '<div class="busqueda-cabecera"><h2>' + (n ? n + (n === 1 ? ' resultado' : ' resultados') + ' para «' + esc(E.q.trim()) + '»' : 'Nada para «' + esc(E.q.trim()) + '»') + '</h2>' +
        '<span>' + esc(textoFecha()) + ' · ' + (E.presupuesto === 0 ? 'Planes gratis' : 'Hasta S/ ' + E.presupuesto + ' para 2') + '</span></div>';
      if (n) {
        html += '<div class="grilla">' + c.encontrados.map(tarjeta).join('') + '</div>';
      } else {
        const sinFiltros = PLANES.filter((p) => coincide(p, c.palabras)).length;
        html += '<div class="vacio">' + (sinFiltros
          ? 'Hay ' + sinFiltros + (sinFiltros === 1 ? ' plan' : ' planes') + ' con esa búsqueda, pero no entran en tu fecha o presupuesto.<button type="button" class="btn-play" data-accion="sin-filtros">Buscar en toda la semana y hasta S/ 250</button>'
          : 'No encontramos nada con esa palabra. Prueba con un distrito (Miraflores, Barranco), un tipo de plan (concierto, café) o «gratis».') + '</div>';
      }
      $('filas').innerHTML = html;
      return;
    }

    if (!c.planes.length) { $('filas').innerHTML = ''; return; }

    const filas = [];
    const top = c.planes.slice(0, 12);
    filas.push(['f-top', (E.presupuesto === 0 ? 'Lo mejor sin gastar un sol' : 'Lo mejor con S/ ' + E.presupuesto), top]);
    const usados = new Set();
    GRUPOS.forEach(([t, prueba], i) => {
      const items = c.planes.filter((p) => !usados.has(p.id) && prueba(p));
      items.forEach((p) => usados.add(p.id));
      if (items.length) filas.push(['f-' + i, t, items]);
    });
    filas.forEach(([id, t, items], i) => {
      html += fila(id, t, items);
      if (i === 0 && c.planes.length > 1) {
        html += '<div class="pausa"><button type="button" class="banner-ruleta" data-accion="abrir-ruleta">' +
          '<span class="mini-ruleta" aria-hidden="true"></span><span class="txt"><strong>¿Siguen sin decidirse?</strong>' +
          '<span>Giren la ruleta con ' + Math.min(c.planes.length, MAX_RULETA) + ' de sus planes y que decida la suerte</span></span><em>Girar</em></button></div>';
      }
      if (i === 1) {
        html += '<div class="pausa"><!-- ESPACIO PUBLICITARIO: reemplaza este div por tu bloque de AdSense --><div class="anuncio"><small>PUBLICIDAD</small>Espacio para anunciante</div></div>';
      }
    });

    const cats = [['Conciertos', 'concierto', 'cultural'], ['Fútbol y deporte', 'futbol', 'aire'], ['Teatro y stand up', 'teatro', 'cultural'],
      ['Planes gratis', 'gratis', 'gratis'], ['Comida', 'comida', 'restaurantes'], ['Aire libre', 'deporte', 'aire']];
    html += '<section class="fila" aria-label="Explorar por categoría"><div class="fila-titulo"><h2>Explorar por categoría</h2></div><div class="carrusel categorias">' +
      cats.map(([t, ilus, v]) => '<button type="button" class="categoria" data-accion="atajo" data-valor="' + v + '"><div class="portada-plan"><svg viewBox="0 0 300 160" preserveAspectRatio="xMidYMid slice" aria-hidden="true">' + ILUS[ilus] + '</svg></div><b>' + t + '</b></button>').join('') +
      '</div></section>';
    $('filas').innerHTML = html;
  }

  // ---------- Render general ----------
  function render() {
    const c = calcular();
    renderHero(c);
    renderFiltros(c);
    renderFilas(c);
    document.body.classList.toggle('buscando', c.palabras.length > 0);
    if (ACTUALIZADO) {
      const d = new Date(ACTUALIZADO);
      $('actualizado').textContent = 'Eventos actualizados: ' + d.toLocaleString('es-PE', { timeZone: 'America/Lima', dateStyle: 'medium', timeStyle: 'short' }) + ' · Precios referenciales.';
    }
  }

  // ---------- Ruleta (ventana) ----------
  const MAX_RULETA = 12;
  const COLORES_RULETA = [['#FFC933', '#1B1036'], ['#D42F1A', '#FFFFFF'], ['#00745C', '#FFFFFF'], ['#5B3FE0', '#FFFFFF'],
    ['#FF8FB1', '#1B1036'], ['#3DB7FF', '#1B1036'], ['#FFFFFF', '#1B1036'], ['#B8E15A', '#1B1036'],
    ['#FFB547', '#1B1036'], ['#C9A7FF', '#1B1036'], ['#5EE6B5', '#1B1036'], ['#9AD0FF', '#1B1036']];
  const R = { abierta: false, segs: [], total: 0, rot: 0, girando: false, ganador: null, origen: null };

  function mezclar(lista) {
    const a = lista.slice();
    for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; }
    return a;
  }
  function cargarRuleta() {
    const c = calcular();
    const base = c.palabras.length ? c.encontrados : c.planes;
    R.total = base.length;
    R.segs = mezclar(base).slice(0, MAX_RULETA);
    R.ganador = null;
  }
  function abrirRuleta(origen) {
    R.origen = origen || null;
    cargarRuleta();
    R.abierta = true;
    document.body.classList.add('con-modal');
    renderRuleta();
    const b = $('ruleta-modal').querySelector('.boton-girar');
    if (b) b.focus();
  }
  function cerrarRuleta() {
    if (R.girando) return;
    R.abierta = false;
    document.body.classList.remove('con-modal');
    $('ruleta-modal').innerHTML = '';
    $('ruleta-modal').hidden = true;
    if (R.origen && document.contains(R.origen)) R.origen.focus();
  }
  function corto(nombre) {
    const limpio = nombre.replace(/\s*[|:(–-].*$/, '').trim() || nombre;
    return limpio.length > 20 ? limpio.slice(0, 19) + '…' : limpio;
  }
  function renderRuleta() {
    const m = $('ruleta-modal');
    m.hidden = !R.abierta;
    if (!R.abierta) return;
    const segs = R.segs;
    const n = segs.length;
    const ang = n ? 360 / n : 360;
    const fondo = n ? 'conic-gradient(' + segs.map((p, i) => COLORES_RULETA[i % 12][0] + ' ' + (i * ang) + 'deg ' + ((i + 1) * ang) + 'deg').join(',') + ')' : '#3A2E6B';
    const etiquetas = segs.map((p, i) => '<span class="etiqueta-seg" style="transform:rotate(' + (i * ang + ang / 2 - 90) + 'deg);color:' + COLORES_RULETA[i % 12][1] + ';font-size:' + (n > 8 ? 11 : 12.5) + 'px">' + esc(corto(p.nombre)) + '</span>').join('');
    const g = R.ganador;
    const resumen = textoFecha() + ' · ' + (E.presupuesto === 0 ? 'Planes gratis' : 'Hasta S/ ' + E.presupuesto + ' para 2') + (E.romantico ? ' · Cena romántica' : '') + (E.q.trim() ? ' · «' + esc(E.q.trim()) + '»' : '');
    m.innerHTML = '<div class="modal-fondo" data-accion="cerrar-ruleta"></div>' +
      '<div class="modal" role="dialog" aria-modal="true" aria-labelledby="ruleta-titulo">' +
      '<button type="button" class="modal-cerrar" data-accion="cerrar-ruleta" aria-label="Cerrar">✕</button>' +
      '<div class="modal-cabeza"><h2 id="ruleta-titulo">Que decida la ruleta</h2><span>' + esc(resumen) + '</span></div>' +
      (n < 2 ? '<p class="modal-vacio">Necesitamos al menos 2 planes para girar. Quita algún filtro o sube un poco el monto.</p>' :
      '<div class="ruleta-caja"><svg class="puntero" width="44" height="38" viewBox="0 0 44 38" aria-hidden="true"><path d="M22 36 L3 3 L41 3 Z" fill="#FFC933" stroke="#1B1036" stroke-width="4" stroke-linejoin="round"/></svg>' +
      '<div class="ruleta" id="ruleta" role="img" aria-label="Ruleta con ' + n + ' planes" style="background:' + fondo + ';transform:rotate(' + R.rot + 'deg)">' + etiquetas + '<span class="centro"></span></div>' +
      '<div class="confeti" id="confeti" aria-hidden="true"></div></div>' +
      '<div aria-live="polite" class="modal-resultado">' + (g
        ? '<div class="tarjeta-ganador"><div class="mini">' + portada(g) + '</div><div class="info"><small>SU PLANCITO ES</small><b>' + esc(g.nombre) + '</b><span>' + esc(cuando(g)) + ' · ' + soles(total(g)) + (total(g) ? ' para dos' : '') + '</span></div>' +
          '<div class="acciones"><a class="btn-play"' + enlace(g) + '>' + esc(textoBoton(g)) + '</a><a class="btn-whatsapp" href="' + compartir(g) + '" target="_blank" rel="noopener">WhatsApp</a></div></div>'
        : '<p class="pista">' + (R.girando ? 'Girando…' : n + ' planes en la ruleta' + (R.total > n ? ' (elegidos al azar de ' + R.total + ')' : '')) + '</p>') + '</div>' +
      '<div class="modal-botones"><button type="button" class="boton-girar" data-accion="girar"' + (R.girando ? ' disabled' : '') + '>' + (R.girando ? 'Girando…' : g ? 'Girar otra vez' : 'Girar la ruleta') + '</button>' +
      (R.total > n ? '<button type="button" class="btn-gris" data-accion="mezclar"' + (R.girando ? ' disabled' : '') + '>Cambiar planes</button>' : '') + '</div>') +
      '</div>';
  }
  function girar() {
    const n = R.segs.length;
    if (R.girando || n < 2) return;
    const ang = 360 / n;
    const idx = Math.floor(Math.random() * n);
    const centro = idx * ang + ang / 2;
    R.rot = R.rot - (R.rot % 360) + 360 * 5 + (360 - centro);
    R.girando = true;
    R.ganador = null;
    const m = $('ruleta-modal');
    m.querySelectorAll('.modal-botones button').forEach((x) => { x.disabled = true; });
    const bg = m.querySelector('.boton-girar');
    if (bg) bg.textContent = 'Girando…';
    const res = m.querySelector('.modal-resultado');
    if (res) res.innerHTML = '<p class="pista">Girando…</p>';
    const rueda = $('ruleta');
    if (rueda) rueda.style.transform = 'rotate(' + R.rot + 'deg)';
    const espera = window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 100 : 3500;
    setTimeout(() => {
      R.girando = false;
      R.ganador = R.segs[idx];
      renderRuleta();
      confeti();
      const b = $('ruleta-modal').querySelector('.boton-girar');
      if (b) b.focus();
    }, espera);
  }
  function confeti() {
    const caja = $('confeti');
    if (!caja || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const colores = ['#FFC933', '#FF4F3A', '#00A884', '#7B61FF', '#FF8FB1', '#3DB7FF'];
    caja.innerHTML = Array.from({ length: 40 }, (_, i) => {
      const x = Math.round((Math.random() - 0.5) * 420) + 'px';
      const y = Math.round((Math.random() - 0.7) * 380) + 'px';
      return '<i style="background:' + colores[i % colores.length] + ';--x:' + x + ';--y:' + y + ';--r:' + Math.round(Math.random() * 720) + 'deg"></i>';
    }).join('');
    setTimeout(() => { caja.innerHTML = ''; }, 1500);
  }

  // ---------- Hero automático ----------
  let temporizador = null;
  function rotarHero() {
    clearInterval(temporizador);
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    temporizador = setInterval(() => {
      if (E.q || document.hidden || E.calAbierto || R.abierta || CITA.abierta) return;
      const n = destacados(calcular()).length;
      if (n > 1) { E.heroIdx = (E.heroIdx + 1) % n; renderHero(calcular()); }
    }, 8000);
  }

  // ---------- Buscador de la barra ----------
  const form = $('busqueda');
  const input = $('q');
  function abrirBusqueda() { form.classList.add('abierta'); input.focus(); }
  function aplicarBusqueda() {
    E.q = input.value;
    form.classList.toggle('con-texto', !!E.q);
    render();
  }
  $('busqueda-icono').addEventListener('click', () => {
    if (form.classList.contains('abierta') && input.value) aplicarBusqueda(); else abrirBusqueda();
  });
  $('busqueda-limpiar').addEventListener('click', () => { input.value = ''; aplicarBusqueda(); input.focus(); });
  input.addEventListener('input', aplicarBusqueda);
  input.addEventListener('blur', () => { if (!input.value) form.classList.remove('abierta'); });
  form.addEventListener('submit', (ev) => { ev.preventDefault(); input.blur(); window.scrollTo({ top: 0, behavior: 'smooth' }); });

  window.addEventListener('scroll', () => { $('barra').classList.toggle('solida', window.scrollY > 40); }, { passive: true });


  // ---------- Para una cita: ranking de 15 + según lo que le gusta a ella ----------
  const CITA = { abierta: false, gusto: 'cenar', tope: 'todos', origen: null };
  const GUSTOS = [
    ['cenar', 'Cena para sorprenderla', 'Los restaurantes mejor calificados', '<path d="M8 3v18M5 3v6a3 3 0 0 0 6 0V3"/><path d="M17 21V3c-2 1-3 4-3 7h3"/>'],
    ['bailar', 'Le gusta bailar', 'Bares y fiestas', '<path d="M9 18V5l11-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="17" cy="16" r="3"/>'],
    ['leer', 'Le encanta leer y lo cultural', 'Museos, teatro, expos y librerías', '<path d="M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2z"/><path d="M4 19V5"/>'],
    ['aire', 'Sorprenderla al aire libre', 'Full days, paseos y planes gratis', '<path d="M12 3l6 9h-4l4 6H6l4-6H6z"/><path d="M12 18v4"/>'],
    ['cafe', 'Es de cafecito y conversar', 'Cafés con buena nota', '<path d="M4 9h12v5a5 5 0 0 1-5 5H9a5 5 0 0 1-5-5z"/><path d="M16 11h2a2 2 0 0 1 0 4h-2"/>'],
    ['reir', 'Le encanta reír', 'Stand up y comedia', '<circle cx="12" cy="12" r="9"/><path d="M8 14s1.5 2 4 2 4-2 4-2M9 9h.01M15 9h.01"/>']
  ];
  const TOPES = [['todos', 'Todos'], ['gratis', 'Gratis'], ['100', 'Hasta S/ 100'], ['200', 'Hasta S/ 200'], ['mas', 'Más de S/ 200']];
  const VOTOS_KEY = 'plancito_votos';
  let VOTOS = {};
  try { VOTOS = JSON.parse(localStorage.getItem(VOTOS_KEY) || '{}') || {}; } catch (e) { VOTOS = {}; }
  const claveVoto = (p) => p.url || p.nombre;
  function votar(p, v) {
    const k = claveVoto(p);
    VOTOS[k] = VOTOS[k] === v ? 0 : v;
    try { localStorage.setItem(VOTOS_KEY, JSON.stringify(VOTOS)); } catch (e) { /* sin almacenamiento */ }
  }
  // % de sorpresa: nota de Google ponderada por cantidad de reseñas (un 5.0 con 8 reseñas no le gana a un 4.8 con 5.000)
  function sorpresa(p) {
    const r = p.calificacion || 0;
    const n = p.resenas || 0;
    const base = r ? (n * r + 300 * 4.3) / (n + 300) : 4.45;
    let pct = Math.round(70 + (base - 4.0) * 30 * 1.25);
    if (p.destacado) pct = Math.max(pct, 97);
    return Math.max(60, Math.min(100, pct));
  }
  const proximos14 = () => { const h = hoy(); return Array.from({ length: 14 }, (_, i) => sumarDias(h, i)); };
  const vigente = (p) => p.siempre || proximos14().some((d) => p.inicio <= d && d <= p.fin);
  const porSorpresa = (a, b) => (b.destacado - a.destacado) || (sorpresa(b) - sorpresa(a)) || ((b.resenas || 0) - (a.resenas || 0)) || (a.precio - b.precio);
  // full days: fuera los privados (muy caros) y los que solo salen en otra temporada
  const MES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'set', 'octubre', 'noviembre', 'diciembre'][+hoy().slice(5, 7) - 1];
  const aireBueno = (p) => !/privad/i.test(p.nombre) && !(/(enero|febrero|marzo|abril|mayo|junio|julio|agosto|setiembre|septiembre|octubre|noviembre|diciembre)/i.test(p.salidas || '') && !normal(p.salidas).includes(MES));

  function rankingCita() {
    const lugares = PLANES.filter((p) => p.siempre && !p.ejemplo);
    const tops = lugares.filter((p) => p.destacado).sort(porSorpresa);
    const usados = new Set(tops.map((p) => p.id));
    const resto = (filtro, n) => lugares.filter((p) => !usados.has(p.id) && filtro(p)).sort(porSorpresa).slice(0, n);
    const huecos = Math.max(0, 15 - tops.length);
    const nAire = Math.min(5, Math.round(huecos / 3));
    const rest = resto((p) => p.tipo === 'restaurantes', huecos - nAire);
    rest.forEach((p) => usados.add(p.id));
    const aire = resto((p) => p.tipo === 'aire' && aireBueno(p), nAire);
    return tops.concat(rest, aire).sort(porSorpresa).slice(0, 15);
  }
  function opcionesCita() {
    const tope = (p) => {
      const t = total(p);
      if (CITA.tope === 'gratis') return t === 0;
      if (CITA.tope === '100') return t <= 100;
      if (CITA.tope === '200') return t <= 200;
      if (CITA.tope === 'mas') return t > 200;
      return true;
    };
    const fechaPrimero = (a, b) => (a.siempre - b.siempre) || String(a.inicio || '').localeCompare(String(b.inicio || '')) || porSorpresa(a, b);
    const filtros = {
      cenar: [(p) => p.siempre && p.tipo === 'restaurantes', porSorpresa],
      bailar: [(p) => p.tipo === 'bar' || ['Fiesta', 'Discoteca', 'Karaoke'].includes(p.categoria), porSorpresa],
      leer: [(p) => p.tipo === 'cultural' && /literatura|libro|feria|exposici|museo|teatro|cultura|arte|poes/i.test(normal(p.categoria + ' ' + p.nombre)), fechaPrimero],
      aire: [(p) => p.tipo === 'aire' && (aireBueno(p) || p.destacado), porSorpresa],
      cafe: [(p) => p.tipo === 'cafe', porSorpresa],
      reir: [(p) => /stand ?up|comedia|humor/i.test(normal(p.categoria + ' ' + p.nombre)), fechaPrimero]
    };
    const [f, orden] = filtros[CITA.gusto];
    return PLANES.filter((p) => !p.ejemplo && vigente(p) && f(p) && tope(p)).sort(orden).slice(0, 6);
  }
  function filaRanking(p, i) {
    const pct = sorpresa(p);
    const v = VOTOS[claveVoto(p)] || 0;
    return '<li class="rk-item">' +
      '<span class="rk-num">' + (i + 1) + '</span>' +
      '<a class="rk-foto"' + enlace(p) + ' aria-label="' + esc(p.nombre) + '">' + portada(p) + '</a>' +
      '<div class="rk-info"><b>' + esc(p.nombre) + (p.destacado ? ' <em class="rk-top">TOP</em>' : '') + '</b>' +
      '<span>' + esc(p.categoria || '') + (p.lugar ? ' · ' + esc(p.lugar) : '') + (p.calificacion ? ' · ★ ' + p.calificacion.toFixed(1) : '') + '</span>' +
      '<span class="rk-precio">' + (total(p) ? soles(total(p)) + ' para dos' : 'Gratis') + '</span>' +
      '<div class="rk-barra" aria-hidden="true"><i style="width:' + pct + '%"></i></div></div>' +
      '<div class="rk-lado"><span class="rk-pct"><b>' + pct + '%</b><small>la sorprende</small></span>' +
      '<div class="rk-votos" role="group" aria-label="¿Te gustó ' + esc(p.nombre) + '?">' +
      '<button type="button" class="rk-voto" aria-pressed="' + (v === 1) + '" aria-label="Me gustó" data-accion="voto" data-valor="1" data-id="' + esc(p.id) + '">' + linea('<path d="M7 11v9H4v-9zM7 11l4-8a2 2 0 0 1 3 2l-1 4h5a2 2 0 0 1 2 2.3l-1.2 7A2 2 0 0 1 16.8 20H7"/>') + '</button>' +
      '<button type="button" class="rk-voto no" aria-pressed="' + (v === -1) + '" aria-label="No me gustó" data-accion="voto" data-valor="-1" data-id="' + esc(p.id) + '">' + linea('<path d="M17 13V4h3v9zM17 13l-4 8a2 2 0 0 1-3-2l1-4H6a2 2 0 0 1-2-2.3l1.2-7A2 2 0 0 1 7.2 4H17"/>') + '</button>' +
      '</div></div></li>';
  }
  function renderCita() {
    const m = $('cita');
    m.hidden = !CITA.abierta;
    if (!CITA.abierta) { m.innerHTML = ''; return; }
    const rk = rankingCita();
    const g = GUSTOS.find((x) => x[0] === CITA.gusto);
    const ops = opcionesCita();
    m.innerHTML = '<div class="cita-caja" role="dialog" aria-modal="true" aria-labelledby="cita-titulo">' +
      '<button type="button" class="modal-cerrar" data-accion="cerrar-cita" aria-label="Cerrar">✕</button>' +
      '<header class="cita-cabeza"><span class="eyebrow">Plancito para una cita</span><h2 id="cita-titulo">Los 15 lugares que más sorprenden</h2>' +
      '<p>Restaurantes y planes al aire libre mejor calificados en Lima. El % de sorpresa sale de la nota y la cantidad de reseñas. Dale like a los que te gustaron.</p></header>' +
      '<ol class="rk-lista">' + rk.map(filaRanking).join('') + '</ol>' +
      '<section class="cita-gustos" aria-labelledby="gustos-titulo"><h3 id="gustos-titulo">¿Qué le gusta a ella?</h3>' +
      '<div class="gustos">' + GUSTOS.map(([k, t, d, ic]) => '<button type="button" class="gusto" aria-pressed="' + (CITA.gusto === k) + '" data-accion="gusto" data-valor="' + k + '">' + linea(ic) + '<span><b>' + t + '</b><small>' + d + '</small></span></button>').join('') + '</div>' +
      '<div class="cita-tope" role="group" aria-label="Presupuesto para dos"><span class="mini-etiqueta">Presupuesto para dos</span>' +
      TOPES.map(([k, t]) => '<button type="button" class="chip' + (k === 'gratis' ? ' chip-gratis' : '') + '" aria-pressed="' + (CITA.tope === k) + '" data-accion="cita-tope" data-valor="' + k + '">' + t + '</button>').join('') + '</div>' +
      '<h4>' + esc(g[1]) + ' · ' + ops.length + (ops.length === 1 ? ' opción' : ' opciones') + '</h4>' +
      (ops.length ? '<div class="grilla cita-grilla">' + ops.map(tarjeta).join('') + '</div>'
        : '<div class="vacio">No hay opciones con ese presupuesto. Prueba con «Todos».</div>') +
      '</section></div>';
  }
  function abrirCita(origen) {
    CITA.abierta = true; CITA.origen = origen || null;
    document.body.classList.add('con-modal');
    if (location.hash !== '#para-una-cita') history.replaceState(null, '', '#para-una-cita');
    renderCita();
    const c = $('cita').querySelector('.modal-cerrar'); if (c) c.focus();
  }
  function cerrarCita() {
    CITA.abierta = false;
    document.body.classList.remove('con-modal');
    if (location.hash === '#para-una-cita') history.replaceState(null, '', location.pathname + location.search);
    renderCita();
    if (CITA.origen && document.contains(CITA.origen)) CITA.origen.focus();
  }

  // ---------- Acciones ----------
  function limpiarBusqueda() { input.value = ''; E.q = ''; form.classList.remove('con-texto', 'abierta'); }
  function arriba() { window.scrollTo({ top: 0, behavior: 'smooth' }); }

  document.addEventListener('click', (ev) => {
    const el = ev.target.closest('[data-accion]');
    if (!el) {
      if (E.calAbierto && !ev.target.closest('.fecha-caja')) { E.calAbierto = false; render(); }
      return;
    }
    const v = el.dataset.valor;
    switch (el.dataset.accion) {
      case 'nada': ev.preventDefault(); return;
      case 'calendario': E.calAbierto = !E.calAbierto; break;
      case 'fecha': E.fecha = v; E.calAbierto = false; E.heroIdx = 0; break;
      case 'presupuesto': E.presupuesto = +v; E.heroIdx = 0; break;
      case 'tipo':
        if (v === 'todo') { E.tipos.clear(); E.romantico = false; }
        else if (E.tipos.has(v)) E.tipos.delete(v);
        else E.tipos.add(v);
        if (TIPOS_REALES.every((t) => E.tipos.has(t))) E.tipos.clear();
        E.attrs.clear(); E.heroIdx = 0;
        break;
      case 'romantico': E.romantico = !E.romantico; E.heroIdx = 0; break;
      case 'abrir-ruleta': abrirRuleta(el); return;
      case 'cita': ev.preventDefault(); abrirCita(el); return;
      case 'cerrar-cita': cerrarCita(); return;
      case 'gusto': CITA.gusto = v; renderCita(); return;
      case 'cita-tope': CITA.tope = v; renderCita(); return;
      case 'voto': {
        const p = PLANES.find((x) => x.id === el.dataset.id);
        if (p) { votar(p, +v); renderCita(); const b = $('cita').querySelector('[data-id="' + el.dataset.id + '"][data-valor="' + v + '"]'); if (b) b.focus(); }
        return;
      }
      case 'cerrar-ruleta': cerrarRuleta(); return;
      case 'girar': girar(); return;
      case 'mezclar': if (!R.girando) { cargarRuleta(); renderRuleta(); } return;
      case 'mas-filtros': E.masFiltros = !E.masFiltros; break;
      case 'estrellas': E.estrellas = +v; break;
      case 'attr': if (E.attrs.has(v)) E.attrs.delete(v); else E.attrs.add(v); break;
      case 'hero': E.heroIdx = +v; rotarHero(); break;
      case 'mover': {
        const riel = $(v);
        if (riel) riel.scrollBy({ left: +el.dataset.dir * riel.clientWidth * 0.85, behavior: 'smooth' });
        return;
      }
      case 'inicio':
        ev.preventDefault();
        limpiarBusqueda(); E.tipos.clear(); E.attrs.clear(); E.estrellas = 0; E.romantico = false; E.heroIdx = 0;
        render(); arriba(); return;
      case 'atajo':
        ev.preventDefault();
        limpiarBusqueda(); E.tipos.clear(); E.attrs.clear(); E.romantico = false; E.heroIdx = 0;
        if (v === 'gratis') E.presupuesto = 0;
        else if (v === 'romantico') { E.romantico = true; if (E.presupuesto < 100) E.presupuesto = 150; }
        else { E.tipos.add(v); if (E.presupuesto === 0) E.presupuesto = 150; }
        render(); arriba(); return;
      case 'sin-filtros':
        E.fecha = 'semana'; E.presupuesto = 250; E.tipos.clear(); E.attrs.clear(); E.estrellas = 0; E.romantico = false;
        break;
      default: return;
    }
    render();
  });

  document.addEventListener('keydown', (ev) => {
    if (ev.key === 'Escape' && R.abierta) { cerrarRuleta(); return; }
    if (ev.key === 'Escape' && CITA.abierta) { cerrarCita(); return; }
    if (ev.key === 'Escape') {
      if (E.calAbierto) { E.calAbierto = false; render(); return; }
      if (document.activeElement === input) { limpiarBusqueda(); render(); input.blur(); }
    }
    if (ev.key === '/' && document.activeElement !== input && !/INPUT|TEXTAREA/.test(document.activeElement.tagName)) {
      ev.preventDefault(); abrirBusqueda();
    }
  });

  window.addEventListener('hashchange', () => { if (location.hash === '#para-una-cita' && !CITA.abierta) abrirCita(); });
  cargar();
  rotarHero();
})();
