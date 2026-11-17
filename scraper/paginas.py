"""
Plancito: genera páginas fijas en HTML para que Google (y su IA) puedan leer los planes.

La web principal (index.html) arma todo con JavaScript, así que Google ve muy poco texto.
Este script lee los mismos datos y escribe:

- planes/<tema>/index.html  → una página por búsqueda típica ("planes gratis en Lima",
                               "qué hacer en Barranco", "conciertos en Lima", etc.)
- sitemap.xml                → la lista de páginas para Google
- robots.txt                 → permite a todos los buscadores y apunta al sitemap

Se corre solo después del scraper (GitHub Actions) y cuando cambias data/manual/.
Para correrlo a mano:  python scraper/paginas.py
Usa solo la librería estándar de Python.
"""
from __future__ import annotations

import html
import json
import re
import shutil
import unicodedata
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DATA = RAIZ / "data"
SALIDA = RAIZ / "planes"
DOMINIO = "https://plancitopes.com"
LIMA = timezone(timedelta(hours=-5))
HOY = datetime.now(LIMA).date()
MAX_ITEMS = 60          # planes por página
MAX_SCHEMA = 30         # planes dentro del JSON-LD
PERSONAS = 2

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
DIAS_C = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]


# ---------------------------------------------------------------- utilidades
def esc(t) -> str:
    return html.escape(str(t or ""), quote=True)


def norm(t: str) -> str:
    t = unicodedata.normalize("NFD", str(t or "").lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def fecha(s):
    try:
        return date.fromisoformat(str(s)[:10])
    except ValueError:
        return None


def larga(d: date) -> str:
    return f"{d.day} de {MESES[d.month - 1]}"


def corta(d: date) -> str:
    return f"{DIAS_C[d.weekday()]} {d.day} {MESES[d.month - 1][:3]}"


def soles(n) -> str:
    n = float(n or 0)
    return f"S/ {n:,.0f}" if n == int(n) else f"S/ {n:,.2f}"


def hora_24(h: str):
    m = re.match(r"\s*(\d{1,2})(?::(\d{2}))?\s*([ap])\.?\s*m", str(h or ""), re.I)
    if not m:
        return None
    hh, mm = int(m.group(1)) % 12, int(m.group(2) or 0)
    if m.group(3).lower() == "p":
        hh += 12
    return f"{hh:02d}:{mm:02d}"


def leer(nombre: str, clave: str) -> list:
    p = DATA / nombre
    if not p.exists():
        return []
    d = json.loads(p.read_text(encoding="utf-8"))
    return d.get(clave, []) if isinstance(d, dict) else d if isinstance(d, list) else []


def valido(x: dict) -> bool:
    return bool(x.get("nombre")) and bool(x.get("url")) and not x.get("ejemplo")


# ---------------------------------------------------------------- datos
def cargar():
    eventos = [e for e in leer("eventos.json", "eventos") + leer("manual/eventos.json", "eventos") if valido(e)]
    eventos = [e for e in eventos if (fecha(e.get("fin")) or fecha(e.get("inicio")) or HOY) >= HOY]
    vistos, ev = set(), []
    for e in sorted(eventos, key=lambda e: (e.get("inicio") or "", norm(e["nombre"]))):
        if e["url"] in vistos:
            continue
        vistos.add(e["url"])
        e["_es_evento"] = True
        ev.append(e)
    lugares = [l for l in leer("lugares.json", "lugares") + leer("manual/lugares.json", "lugares") if valido(l)]
    vistos, lu = set(), []
    for l in lugares:
        if l["url"] in vistos:
            continue
        vistos.add(l["url"])
        lu.append(l)
    return ev, lu


def en_rango(e, ini: date, fin: date) -> bool:
    a = fecha(e.get("inicio")) or HOY
    b = fecha(e.get("fin")) or a
    return a <= fin and b >= ini


def en_zona(x, *nombres) -> bool:
    lugar = norm(x.get("lugar"))
    return any(norm(n) in lugar for n in nombres)


def cat(x, *cats) -> bool:
    return norm(x.get("categoria")) in {norm(c) for c in cats}


def precio(x):
    try:
        return float(x.get("precio"))
    except (TypeError, ValueError):
        return None


def por_calificacion(lista):
    return sorted(lista, key=lambda l: (-(l.get("calificacion") or 0), precio(l) or 0))


def cuando(e) -> str:
    if not e.get("_es_evento"):
        return "Toda la semana" if e.get("categoria") in ("Restaurante", "Café", "Bar") else ""
    a, b = fecha(e.get("inicio")), fecha(e.get("fin"))
    h = (" · " + e["hora"]) if e.get("hora") else ""
    if not a:
        return ""
    if b and b > a:
        return (f"Hasta el {corta(b)}" if a <= HOY else f"Del {corta(a)} al {corta(b)}") + h
    return corta(a) + h


# ---------------------------------------------------------------- temas (una página por búsqueda)
def temas(ev, lu):
    vie = HOY + timedelta(days=(4 - HOY.weekday()) % 7) if HOY.weekday() < 5 else HOY - timedelta(days=HOY.weekday() - 4)
    dom = vie + timedelta(days=2)
    finde_ini = max(vie, HOY)
    todos = ev + lu
    gratis_ev = [e for e in ev if precio(e) == 0]
    gratis_lu = [l for l in lu if precio(l) == 0]

    def zona(slug, nombre, *claves, extra=""):
        evz = [e for e in ev if en_zona(e, *claves)]
        luz = por_calificacion([l for l in lu if en_zona(l, *claves)])
        return dict(
            slug=slug, grupo="Por distrito",
            titulo=f"Qué hacer en {nombre}: planes, eventos y dónde comer",
            h1=f"Qué hacer en {nombre}",
            desc=f"Planes en {nombre} actualizados cada día: eventos, conciertos, teatro, restaurantes, cafés y bares con precio para dos.",
            intro=f"Hoy tenemos {len(evz)} eventos" + (f" y {len(luz)} restaurantes, cafés y bares" if luz else "")
                  + f" en {nombre}{extra}, con precio por persona y para dos. La lista se actualiza todos los días.",
            items=evz + luz,
            faq=[(f"¿Qué hacer en {nombre} gratis?",
                  f"Ahora hay {sum(1 for e in evz if precio(e) == 0)} planes gratis en {nombre}. Están marcados como «Gratis» en la lista."),
                 (f"¿Dónde comer rico en {nombre}?",
                  f"Los restaurantes, cafés y bares de esta página tienen 4.5 estrellas o más en Google Maps." if luz else
                  f"Mira la página de restaurantes de Lima para más opciones.")])

    return [
        dict(slug="planes-gratis-lima", grupo="Destacados",
             titulo="Planes gratis en Lima hoy y este fin de semana",
             h1="Planes gratis en Lima",
             desc=f"{len(gratis_ev) + len(gratis_lu)} planes gratis en Lima: conciertos, exposiciones, cine, charlas y paseos. Actualizado cada día.",
             intro=f"Hay {len(gratis_ev) + len(gratis_lu)} planes gratis en Lima ahora mismo: conciertos, exposiciones, cine, "
                   f"charlas y más. Revisamos las agendas de Lima todos los días.",
             items=gratis_ev + gratis_lu,
             faq=[("¿Qué hacer gratis en Lima este fin de semana?",
                   f"Del {larga(finde_ini)} al {larga(dom)} hay {sum(1 for e in gratis_ev if en_rango(e, finde_ini, dom))} eventos gratis. Puedes verlos en la página de planes de este fin de semana."),
                  ("¿Hay que reservar en los planes gratis?",
                   "Algunos piden inscripción previa porque el aforo es limitado. Entra al enlace de cada plan para ver si hace falta.")]),
        dict(slug="planes-este-fin-de-semana-lima", grupo="Destacados",
             titulo=f"Planes este fin de semana en Lima ({finde_ini.day} al {larga(dom)})",
             h1="Planes para este fin de semana en Lima",
             desc=f"Qué hacer en Lima del {larga(finde_ini)} al {larga(dom)}: conciertos, teatro, stand up, cine y planes gratis, con precio para dos.",
             intro=f"Del {DIAS[finde_ini.weekday()]} {larga(finde_ini)} al domingo {larga(dom)} hay "
                   f"{sum(1 for e in ev if en_rango(e, finde_ini, dom))} eventos en Lima. Abajo están ordenados por fecha, con precio para dos.",
             items=[e for e in ev if en_rango(e, finde_ini, dom)],
             faq=[("¿Qué hacer en Lima este fin de semana con poco presupuesto?",
                   f"Hay {sum(1 for e in ev if en_rango(e, finde_ini, dom) and precio(e) == 0)} planes gratis y "
                   f"{sum(1 for e in ev if en_rango(e, finde_ini, dom) and (precio(e) or 0) * PERSONAS <= 100)} que cuestan S/ 100 o menos para dos.")]),
        dict(slug="planes-hoy-lima", grupo="Destacados",
             titulo=f"Qué hacer hoy en Lima ({DIAS[HOY.weekday()]} {larga(HOY)})",
             h1="Qué hacer hoy en Lima",
             desc=f"Planes para hoy {DIAS[HOY.weekday()]} {larga(HOY)} en Lima: eventos, conciertos, teatro, cine y planes gratis.",
             intro=f"Hoy, {DIAS[HOY.weekday()]} {larga(HOY)}, hay {sum(1 for e in ev if en_rango(e, HOY, HOY))} eventos en Lima.",
             items=[e for e in ev if en_rango(e, HOY, HOY)], faq=[]),
        dict(slug="planes-con-100-soles-lima", grupo="Por presupuesto",
             titulo="Planes en Lima con S/ 100 para dos",
             h1="Planes en Lima con S/ 100 para dos",
             desc="Planes en Lima que cuestan S/ 100 o menos para dos personas: eventos, restaurantes, cafés, bares y planes gratis.",
             intro="Todos estos planes cuestan S/ 100 o menos para dos personas (S/ 50 o menos cada uno).",
             items=[x for x in ev if precio(x) is not None and precio(x) * PERSONAS <= 100]
                   + por_calificacion([l for l in lu if precio(l) is not None and precio(l) * PERSONAS <= 100]),
             faq=[]),
        dict(slug="planes-con-50-soles-lima", grupo="Por presupuesto",
             titulo="Planes baratos en Lima: con S/ 50 para dos",
             h1="Planes baratos en Lima con S/ 50 para dos",
             desc="Planes baratos en Lima que cuestan S/ 50 o menos para dos personas, incluidos los gratis.",
             intro="Todos estos planes cuestan S/ 50 o menos para dos personas (S/ 25 o menos cada uno).",
             items=[x for x in ev if precio(x) is not None and precio(x) * PERSONAS <= 50]
                   + por_calificacion([l for l in lu if precio(l) is not None and precio(l) * PERSONAS <= 50]),
             faq=[]),
        dict(slug="conciertos-lima", grupo="Por tipo de plan",
             titulo="Conciertos en Lima: próximas fechas y precios",
             h1="Conciertos en Lima", desc="Próximos conciertos y festivales en Lima con fecha, lugar y precio para dos.",
             intro="Los próximos conciertos y festivales en Lima, ordenados por fecha.",
             items=[e for e in ev if cat(e, "Concierto", "Festival")], faq=[]),
        dict(slug="teatro-lima", grupo="Por tipo de plan",
             titulo="Obras de teatro en Lima: cartelera y precios",
             h1="Teatro en Lima", desc="Cartelera de teatro, danza y shows en Lima con fecha, sala y precio para dos.",
             intro="Obras de teatro, danza y shows en cartelera en Lima.",
             items=[e for e in ev if cat(e, "Teatro", "Danza", "Show")], faq=[]),
        dict(slug="stand-up-comedy-lima", grupo="Por tipo de plan",
             titulo="Stand up comedy en Lima: próximas funciones",
             h1="Stand up comedy en Lima", desc="Próximas funciones de stand up comedy en Lima con fecha, lugar y precio para dos.",
             intro="Las próximas funciones de stand up en Lima, ordenadas por fecha.",
             items=[e for e in ev if cat(e, "Stand up")], faq=[]),
        dict(slug="exposiciones-lima", grupo="Por tipo de plan",
             titulo="Exposiciones y museos en Lima: qué ver ahora",
             h1="Exposiciones en Lima", desc="Exposiciones de arte, historia, arqueología y diseño en Lima. Muchas son gratis.",
             intro="Exposiciones de arte, historia, arqueología y diseño abiertas en Lima. Muchas tienen ingreso libre.",
             items=[e for e in ev if cat(e, "Exposición", "Artes visuales", "Arqueología", "Historia", "Diseño")], faq=[]),
        dict(slug="cine-lima", grupo="Por tipo de plan",
             titulo="Cine en Lima: funciones especiales y ciclos",
             h1="Cine en Lima", desc="Funciones de cine, ciclos y cine al aire libre en Lima, muchas gratis.",
             intro="Funciones especiales, ciclos y cine en centros culturales de Lima.",
             items=[e for e in ev if e.get("tipo") == "cine"], faq=[]),
        dict(slug="planes-con-ninos-lima", grupo="Por tipo de plan",
             titulo="Planes con niños en Lima",
             h1="Planes con niños en Lima", desc="Planes para ir con niños en Lima: obras, talleres, cine y actividades para la familia.",
             intro="Obras, talleres y actividades para ir con niños en Lima.",
             items=[e for e in ev if cat(e, "Kids", "Taller")], faq=[]),
        dict(slug="full-days-desde-lima", grupo="Por tipo de plan",
             titulo="Full days desde Lima: escapadas de un día y precios",
             h1="Full days desde Lima", desc="Full days y escapadas de un día desde Lima: Lunahuaná, Huacachina, Antioquía, Lachay y más, con precio.",
             intro="Escapadas de un día que salen desde Lima, con precio por persona y para dos.",
             items=por_calificacion([l for l in lu if cat(l, "Full day")]), faq=[]),
        dict(slug="tours-lima", grupo="Por tipo de plan",
             titulo="Tours y free tours en Lima",
             h1="Tours en Lima", desc="Tours y free tours por Lima: Centro Histórico, Barranco, Miraflores y más.",
             intro="Tours guiados y free tours por Lima.",
             items=por_calificacion([l for l in lu if cat(l, "Tour", "Free tour")]), faq=[]),
        dict(slug="restaurantes-lima", grupo="Para comer y tomar algo",
             titulo="Restaurantes en Lima con 4.5 estrellas o más, con precio para dos",
             h1="Restaurantes en Lima", desc="Restaurantes de Lima con 4.5 estrellas o más en Google Maps, con precio aproximado para dos.",
             intro="Restaurantes de Miraflores, San Isidro, San Borja y Surco con 4.5 estrellas o más en Google Maps.",
             items=por_calificacion([l for l in lu if cat(l, "Restaurante")]), faq=[]),
        dict(slug="cafes-lima", grupo="Para comer y tomar algo",
             titulo="Cafés en Lima con 4.5 estrellas o más",
             h1="Cafés en Lima", desc="Cafés de Lima con 4.5 estrellas o más en Google Maps, con precio aproximado para dos.",
             intro="Cafés de Miraflores, San Isidro, San Borja y Surco con 4.5 estrellas o más en Google Maps.",
             items=por_calificacion([l for l in lu if cat(l, "Café")]), faq=[]),
        dict(slug="bares-lima", grupo="Para comer y tomar algo",
             titulo="Bares en Lima con 4.5 estrellas o más",
             h1="Bares en Lima", desc="Bares de Lima con 4.5 estrellas o más en Google Maps, con precio aproximado para dos.",
             intro="Bares de Miraflores, San Isidro, San Borja y Surco con 4.5 estrellas o más en Google Maps.",
             items=por_calificacion([l for l in lu if cat(l, "Bar")]), faq=[]),
        zona("que-hacer-en-miraflores", "Miraflores", "Miraflores"),
        zona("que-hacer-en-barranco", "Barranco", "Barranco"),
        zona("que-hacer-en-surco", "Surco", "Surco"),
        zona("que-hacer-en-san-isidro", "San Isidro", "San Isidro"),
        zona("que-hacer-en-san-borja", "San Borja", "San Borja"),
        zona("que-hacer-en-el-centro-de-lima", "el Centro de Lima", "Cercado de Lima", "Centro de Lima", "Centro Histórico"),
    ]


# ---------------------------------------------------------------- JSON-LD
TIPO_SCHEMA = {"Restaurante": "Restaurant", "Café": "CafeOrCoffeeShop", "Bar": "BarOrPub",
               "Full day": "TouristTrip", "Tour": "TouristTrip", "Free tour": "TouristTrip"}


def schema_item(x):
    p = precio(x)
    if x.get("_es_evento"):
        a = fecha(x.get("inicio")) or HOY
        h = hora_24(x.get("hora"))
        obj = {"@type": "Event", "name": x["nombre"],
               "startDate": f"{a.isoformat()}T{h}-05:00" if h else a.isoformat(),
               "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
               "eventStatus": "https://schema.org/EventScheduled",
               "location": {"@type": "Place", "name": x.get("lugar") or "Lima",
                            "address": {"@type": "PostalAddress", "addressLocality": x.get("lugar") or "Lima",
                                        "addressRegion": "Lima", "addressCountry": "PE"}},
               "url": x["url"]}
        if fecha(x.get("fin")) and fecha(x.get("fin")) != a:
            obj["endDate"] = x["fin"]
        if x.get("imagen"):
            obj["image"] = x["imagen"]
        if p is not None:
            obj["isAccessibleForFree"] = p == 0
            obj["offers"] = {"@type": "Offer", "price": p, "priceCurrency": "PEN", "url": x["url"],
                             "availability": "https://schema.org/InStock"}
        return obj
    obj = {"@type": TIPO_SCHEMA.get(x.get("categoria"), "TouristAttraction"), "name": x["nombre"], "url": x["url"]}
    if obj["@type"] != "TouristTrip":
        obj["address"] = {"@type": "PostalAddress", "addressLocality": x.get("lugar") or "Lima",
                          "addressRegion": "Lima", "addressCountry": "PE"}
    if x.get("imagen"):
        obj["image"] = x["imagen"]
    return obj


def json_ld(t, items, url):
    datos = [
        {"@context": "https://schema.org", "@type": "CollectionPage", "name": t["h1"], "description": t["desc"],
         "url": url, "inLanguage": "es-PE", "dateModified": HOY.isoformat(),
         "isPartOf": {"@type": "WebSite", "name": "Plancito", "url": DOMINIO + "/"},
         "mainEntity": {"@type": "ItemList", "numberOfItems": len(items),
                        "itemListElement": [{"@type": "ListItem", "position": i + 1, "item": schema_item(x)}
                                            for i, x in enumerate(items[:MAX_SCHEMA])]}},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Plancito", "item": DOMINIO + "/"},
            {"@type": "ListItem", "position": 2, "name": "Planes en Lima", "item": DOMINIO + "/planes/"},
            {"@type": "ListItem", "position": 3, "name": t["h1"], "item": url}]},
    ]
    txt = json.dumps(datos, ensure_ascii=False, indent=1).replace("</", "<\\/")
    return f'<script type="application/ld+json">\n{txt}\n</script>'


# ---------------------------------------------------------------- HTML
def tarjeta(x, base):
    p = precio(x)
    if p is None:
        precio_txt = ""
    elif p == 0:
        precio_txt = '<b class="sp-gratis">Gratis</b>'
    else:
        precio_txt = f"<b>{soles(p * PERSONAS)} para dos</b> <span>({soles(p)} por persona)</span>"
    img = x.get("imagen_local")
    foto = (f'<img src="{base}{esc(img)}" alt="" width="160" height="100" loading="lazy" decoding="async">'
            if img else '<span class="sp-sinfoto" aria-hidden="true"></span>')
    detalles = [d for d in (x.get("categoria"), cuando(x), x.get("lugar")) if d]
    cal = f' · ★ {x["calificacion"]:.1f} en Google' if x.get("calificacion") and not x.get("_es_evento") and x.get("fuente") else ""
    accion = "Ver ubicación" if "maps.google" in (x.get("url") or "") else "Ver y comprar"
    return (f'<li class="sp-plan">{foto}<div class="sp-info"><h3>{esc(x["nombre"])}</h3>'
            f'<p class="sp-meta">{esc(" · ".join(detalles))}{esc(cal)}</p>'
            f'<p class="sp-precio">{precio_txt}</p></div>'
            f'<a class="sp-btn" href="{esc(x["url"])}" target="_blank" rel="noopener">{accion} →</a></li>')


def nav_temas(lista, actual, base_planes):
    grupos = {}
    for t in lista:
        grupos.setdefault(t["grupo"], []).append(t)
    out = []
    for g, ts in grupos.items():
        links = "".join(
            f'<li><a href="{base_planes}{t["slug"]}/"' + (' aria-current="page"' if t["slug"] == actual else "")
            + f'>{esc(t["h1"])}</a></li>' for t in ts)
        out.append(f'<div><h3>{esc(g)}</h3><ul>{links}</ul></div>')
    return '<nav class="sp-explora" aria-label="Más planes en Lima"><h2>Más planes en Lima</h2><div class="sp-grupos">' + "".join(out) + "</div></nav>"


def cabecera(titulo, desc, url, base, extra=""):
    return f"""<!doctype html>
<html lang="es-PE">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(titulo)} · Plancito</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:title" content="{esc(titulo)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{url}">
<meta property="og:locale" content="es_PE">
<meta name="theme-color" content="#0F0A1F">
<link rel="icon" href="{base}img/logo.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@600;800&family=Inter:wght@400;500;600;700;800&display=swap">
<link rel="stylesheet" href="{base}estilos.css">
<script src="{base}medicion.js" defer></script>
{extra}
</head>
<body class="pagina-seo">
<header class="barra solida">
  <div class="barra-izq">
    <a href="{base}" class="logo" aria-label="Plancito, inicio"><img src="{base}img/logo.svg" alt="" width="36" height="36"><span>plancito</span></a>
    <nav class="menu" aria-label="Principal">
      <a href="{base}">Inicio</a>
      <a href="{base}planes/planes-gratis-lima/" class="menu-gratis">Planes gratis</a>
      <a href="{base}cita.html" class="menu-cita">Para una cita</a>
      <a href="{base}planes/">Todos los planes</a>
    </nav>
  </div>
</header>
"""


PIE = """<footer class="pie">
  <span>Plancito junta planes de Joinnus, Teleticket, EntradaLibre, Civitatis, Inca Trilogy Tours y Google Maps. Al comprar te llevamos a la página oficial.</span>
  <span>Precios referenciales. Actualizado el {fecha}.</span>
</footer>
</body>
</html>
"""


def pagina_tema(t, lista_temas):
    url = f"{DOMINIO}/planes/{t['slug']}/"
    base = "../../"
    items = t["items"][:MAX_ITEMS]
    if items:
        cuerpo = '<ol class="sp-lista">' + "".join(tarjeta(x, base) for x in items) + "</ol>"
        if len(t["items"]) > MAX_ITEMS:
            cuerpo += f'<p class="sp-nota">Mostramos {MAX_ITEMS} de {len(t["items"])}. <a href="{base}">Usa los filtros de Plancito</a> para ver todos.</p>'
    else:
        cuerpo = ('<p class="sp-nota">En este momento no hay planes de este tipo. La lista se actualiza todos los días; '
                  'mientras tanto, mira las otras páginas de abajo.</p>')
    faq = ""
    if t.get("faq"):
        faq = '<section class="sp-faq"><h2>Preguntas frecuentes</h2>' + "".join(
            f"<h3>{esc(q)}</h3><p>{esc(a)}</p>" for q, a in t["faq"]) + "</section>"
    return (cabecera(t["titulo"], t["desc"], url, base, json_ld(t, items, url))
            + f"""<main class="sp">
  <nav class="sp-migas" aria-label="Ruta"><a href="{base}">Plancito</a> › <a href="{base}planes/">Planes en Lima</a> › <span>{esc(t["h1"])}</span></nav>
  <h1>{esc(t["h1"])}</h1>
  <p class="sp-intro">{esc(t["intro"])}</p>
  <p class="sp-act">Actualizado el {DIAS[HOY.weekday()]} {larga(HOY)} de {HOY.year}. Precios referenciales.</p>
  <p><a class="sp-cta" href="{base}">Filtrar por presupuesto y zona en Plancito →</a></p>
  {cuerpo}
  {faq}
  {nav_temas(lista_temas, t["slug"], base + "planes/")}
</main>
""" + PIE.format(fecha=f"{larga(HOY)} de {HOY.year}"))


def pagina_indice(lista_temas):
    url = f"{DOMINIO}/planes/"
    base = "../"
    desc = "Todos los planes de Lima por tipo, distrito y presupuesto: planes gratis, este fin de semana, conciertos, teatro, restaurantes y más."
    filas = "".join(f'<li><a href="{t["slug"]}/">{esc(t["h1"])}</a> <span>({len(t["items"])})</span></li>' for t in lista_temas)
    return (cabecera("Planes en Lima por tipo, distrito y presupuesto", desc, url, base)
            + f"""<main class="sp">
  <nav class="sp-migas" aria-label="Ruta"><a href="{base}">Plancito</a> › <span>Planes en Lima</span></nav>
  <h1>Planes en Lima</h1>
  <p class="sp-intro">Elige cómo quieres buscar: por tipo de plan, por distrito o por cuánto quieren gastar. Todo se actualiza cada día.</p>
  <ul class="sp-indice">{filas}</ul>
</main>
""" + PIE.format(fecha=f"{larga(HOY)} de {HOY.year}"))


def sitemap(lista_temas):
    urls = [(f"{DOMINIO}/", "daily"), (f"{DOMINIO}/cita.html", "weekly"), (f"{DOMINIO}/planes/", "daily")]
    urls += [(f"{DOMINIO}/planes/{t['slug']}/", "daily") for t in lista_temas]
    filas = "\n".join(f"  <url><loc>{u}</loc><lastmod>{HOY.isoformat()}</lastmod><changefreq>{f}</changefreq></url>"
                      for u, f in urls)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{filas}\n</urlset>\n'


ROBOTS = f"""# Plancito: todos los buscadores pueden leer la web (menos el panel de administración)
User-agent: *
Allow: /
Disallow: /admin.html

Sitemap: {DOMINIO}/sitemap.xml
"""


def main():
    ev, lu = cargar()
    lista = temas(ev, lu)
    if SALIDA.exists():
        shutil.rmtree(SALIDA)
    SALIDA.mkdir()
    for t in lista:
        d = SALIDA / t["slug"]
        d.mkdir()
        (d / "index.html").write_text(pagina_tema(t, lista), encoding="utf-8")
    (SALIDA / "index.html").write_text(pagina_indice(lista), encoding="utf-8")
    # Enlaces a estas páginas al pie de la web principal, para que Google las encuentre
    portada = RAIZ / "index.html"
    if portada.exists():
        txt = portada.read_text(encoding="utf-8")
        bloque = ('<div class="explora-pie">' + nav_temas(lista, None, "planes/")
                  .replace("<h2>Más planes en Lima</h2>", "<h2>Explora planes en Lima</h2>") + "</div>")
        nuevo = re.sub(r"(<!-- EXPLORA:INICIO[^>]*-->).*?(<!-- EXPLORA:FIN -->)",
                       lambda m: m.group(1) + "\n" + bloque + "\n" + m.group(2), txt, flags=re.S)
        if nuevo != txt:
            portada.write_text(nuevo, encoding="utf-8")
    (RAIZ / "sitemap.xml").write_text(sitemap(lista), encoding="utf-8")
    (RAIZ / "robots.txt").write_text(ROBOTS, encoding="utf-8")
    print(f"Páginas: {len(lista)} temas con {len(ev)} eventos y {len(lu)} lugares.")
    for t in lista:
        print(f"  {t['slug']:36} {len(t['items'])}")


if __name__ == "__main__":
    main()
