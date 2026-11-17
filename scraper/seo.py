"""Genera los archivos para buscadores (Google y su IA, ChatGPT, etc.):

- agenda.html: la agenda de la semana en HTML simple (sin JavaScript), con datos
  estructurados schema.org para que Google entienda cada evento.
- sitemap.xml: la lista de páginas del sitio con su fecha de actualización.

Se corre al final del scraper diario, y también a mano:  python scraper/seo.py
"""
import html
import json
from collections import OrderedDict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DATA = RAIZ / "data"
SITIO = "https://plancitopes.com"
LIMA = timezone(timedelta(hours=-5))
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]
NOMBRE_TIPO = {"restaurantes": "Restaurantes", "cafes": "Cafés", "bares": "Bares"}


def leer(ruta, clave):
    try:
        d = json.loads(ruta.read_text(encoding="utf-8"))
        return d.get(clave, []) if isinstance(d, dict) else d
    except (OSError, ValueError):
        return []


def e(t):
    return html.escape(str(t or ""), quote=True)


def precio_txt(p):
    return "Gratis" if not p else f"S/ {round(p):,}".replace(",", " ")


def fecha_larga(d):
    return f"{DIAS[d.weekday()]} {d.day} de {MESES[d.month - 1]}"


def hora_iso(h):
    """'7:00 pm' -> '19:00' (o '' si no se entiende)."""
    try:
        t = datetime.strptime(h.strip().lower().replace(".", ""), "%I:%M %p")
        return t.strftime("%H:%M")
    except (ValueError, AttributeError):
        return ""


def abs_url(ruta):
    if not ruta:
        return ""
    return ruta if ruta.startswith("http") else f"{SITIO}/{ruta.lstrip('/')}"


def evento_ld(ev):
    h = hora_iso(ev.get("hora", ""))
    inicio = ev["inicio"] + (f"T{h}:00-05:00" if h else "")
    lugar = ev.get("lugar") or "Lima"
    partes = [x.strip() for x in lugar.split(" - ") if x.strip()]
    zona = partes[1] if len(partes) >= 3 else (partes[-1] if len(partes) == 2 else "Lima")
    d = {
        "@type": "Event",
        "name": ev["nombre"],
        "startDate": inicio,
        "endDate": ev.get("fin") or ev["inicio"],
        "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
        "eventStatus": "https://schema.org/EventScheduled",
        "location": {"@type": "Place", "name": partes[0] if partes else "Lima",
                     "address": {"@type": "PostalAddress", "addressLocality": zona,
                                 "addressRegion": "Lima", "addressCountry": "PE"}},
        "offers": {"@type": "Offer", "price": ev.get("precio") or 0, "priceCurrency": "PEN",
                   "availability": "https://schema.org/InStock", "url": ev.get("url", "")},
        "url": ev.get("url", ""),
    }
    img = abs_url(ev.get("imagen_local") or "")
    if img:
        d["image"] = [img]
    return d


def main():
    hoy = datetime.now(LIMA).date()
    hasta = hoy + timedelta(days=13)
    eventos = [x for x in leer(DATA / "eventos.json", "eventos") + leer(DATA / "manual" / "eventos.json", "eventos")
               if x.get("nombre") and x.get("inicio")]
    lugares = leer(DATA / "lugares.json", "lugares")

    # Eventos de las próximas dos semanas, agrupados por día (los de varios días, en su primer día visible)
    por_dia = OrderedDict()
    for ev in sorted(eventos, key=lambda x: (x["inicio"], x.get("hora", ""), x["nombre"])):
        try:
            ini = date.fromisoformat(ev["inicio"])
            fin = date.fromisoformat(ev.get("fin") or ev["inicio"])
        except ValueError:
            continue
        if fin < hoy or ini > hasta:
            continue
        dia = max(ini, hoy)
        por_dia.setdefault(dia, []).append(ev)

    gratis = sum(1 for lista in por_dia.values() for ev in lista if not ev.get("precio"))
    total = sum(len(v) for v in por_dia.values())

    bloques = []
    ld_eventos = []
    for dia, lista in por_dia.items():
        filas = []
        for ev in lista[:40]:
            extra = " · ".join(x for x in [ev.get("categoria"), ev.get("hora"), ev.get("lugar")] if x)
            filas.append(
                f'<li><a href="{e(ev.get("url"))}" rel="noopener" target="_blank">{e(ev["nombre"])}</a>'
                f'<span class="dato">{e(extra)}</span><span class="precio">{precio_txt(ev.get("precio"))}</span></li>')
            if len(ld_eventos) < 120:
                ld_eventos.append(evento_ld(ev))
        bloques.append(f'<section><h2>{e(fecha_larga(dia).capitalize())}</h2><ul>{"".join(filas)}</ul></section>')

    # Lugares para ir cualquier día
    def top(tipo, n=8):
        xs = [l for l in lugares if l.get("tipo") == tipo and l.get("fuente") == "Google Maps"]
        xs.sort(key=lambda l: (-(l.get("calificacion") or 0), -(l.get("resenas") or 0)))
        return xs[:n]

    secciones_lugares = []
    for tipo, titulo in [("restaurantes", "Restaurantes mejor calificados"), ("cafes", "Cafés para una buena conversación"),
                         ("bares", "Bares para salir de noche")]:
        xs = top(tipo)
        if not xs:
            continue
        filas = "".join(
            f'<li><a href="{e(l.get("url"))}" rel="noopener" target="_blank">{e(l["nombre"])}</a>'
            f'<span class="dato">{e(l.get("lugar"))} · ★ {l.get("calificacion")} ({l.get("resenas", 0)} reseñas)</span>'
            f'<span class="precio">desde {precio_txt(l.get("precio"))} p/p aprox.</span></li>' for l in xs)
        secciones_lugares.append(f'<section><h2>{titulo}</h2><ul>{filas}</ul></section>')
    full = [l for l in lugares if l.get("categoria") == "Full day"][:10]
    if full:
        filas = "".join(
            f'<li><a href="{e(l.get("url"))}" rel="noopener" target="_blank">{e(l["nombre"])}</a>'
            f'<span class="dato">Sale desde Lima</span><span class="precio">{precio_txt(l.get("precio"))}</span></li>' for l in full)
        secciones_lugares.append(f'<section><h2>Full days para escaparse de Lima</h2><ul>{filas}</ul></section>')

    ld = [
        {"@context": "https://schema.org", "@type": "ItemList", "name": "Agenda de planes en Lima",
         "itemListElement": [{"@type": "ListItem", "position": i + 1, "item": ev} for i, ev in enumerate(ld_eventos)]},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Plancito", "item": SITIO + "/"},
            {"@type": "ListItem", "position": 2, "name": "Agenda de Lima", "item": SITIO + "/agenda.html"}]},
    ]
    rango = f"{hoy.day} de {MESES[hoy.month - 1]} al {hasta.day} de {MESES[hasta.month - 1]}"
    desc = (f"Agenda de Lima del {rango}: {total} conciertos, obras de teatro, stand-up, ferias y planes, "
            f"{gratis} de ellos gratis. Más los mejores restaurantes, cafés y bares de Miraflores, San Isidro, San Borja y Surco.")

    pagina = f"""<!doctype html>
<html lang="es-PE">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Qué hacer en Lima esta semana · Agenda de planes y eventos | Plancito</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{SITIO}/agenda.html">
<meta property="og:title" content="Qué hacer en Lima esta semana · Plancito">
<meta property="og:description" content="{e(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{SITIO}/agenda.html">
<meta property="og:image" content="{SITIO}/img/og.png">
<meta property="og:locale" content="es_PE">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#0F0A1F">
<link rel="icon" href="img/logo.svg" type="image/svg+xml">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
<style>
body{{margin:0;background:#0F0A1F;color:#F4F1FA;font:16px/1.55 Inter,system-ui,sans-serif}}
main{{max-width:860px;margin:0 auto;padding:24px 18px 60px}}
a{{color:#FFD23F}} header a{{color:#F4F1FA;text-decoration:none;font-weight:800;font-size:22px}}
header{{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}}
.boton{{background:#FFD23F;color:#0F0A1F;padding:10px 16px;border-radius:999px;font-weight:800;text-decoration:none}}
h1{{font-size:30px;line-height:1.2;margin:28px 0 8px}} h2{{font-size:20px;margin:32px 0 10px;color:#FF7AB6}}
ul{{list-style:none;padding:0;margin:0}} li{{padding:10px 0;border-bottom:1px solid #2A2242;display:flex;flex-wrap:wrap;gap:4px 12px}}
li a{{font-weight:700;flex:1 1 100%}} .dato{{color:#B9B2CC;font-size:14px}} .precio{{font-weight:700;font-size:14px}}
footer{{color:#8C84A3;font-size:13px;margin-top:40px}}
</style>
</head>
<body>
<main>
<header><a href="./">plancito</a><a class="boton" href="./">Filtrar por presupuesto y zona</a></header>
<h1>Qué hacer en Lima: agenda del {e(rango)}</h1>
<p>{e(desc)} Para filtrar por tu presupuesto, distrito y día, entra a <a href="./">Plancito</a>. ¿Tienes una cita? Mira <a href="cita.html">los lugares que más sorprenden</a>.</p>
{"".join(bloques)}
<h2 style="color:#F4F1FA;font-size:24px;margin-top:48px">Lugares para ir cualquier día</h2>
{"".join(secciones_lugares)}
<footer>Actualizado el {e(fecha_larga(hoy))} de {hoy.year}. Precios referenciales; al comprar vas a la página oficial de cada evento. Restaurantes, cafés y bares: datos de Google Maps.</footer>
</main>
</body>
</html>
"""
    (RAIZ / "agenda.html").write_text(pagina, encoding="utf-8")

    hoy_iso = hoy.isoformat()
    urls = [("", "daily", "1.0"), ("agenda.html", "daily", "0.9"), ("cita.html", "weekly", "0.8")]
    sitemap = ['<?xml version="1.0" encoding="UTF-8"?>',
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for ruta, freq, prio in urls:
        sitemap.append(f"  <url><loc>{SITIO}/{ruta}</loc><lastmod>{hoy_iso}</lastmod>"
                       f"<changefreq>{freq}</changefreq><priority>{prio}</priority></url>")
    sitemap.append("</urlset>")
    (RAIZ / "sitemap.xml").write_text("\n".join(sitemap) + "\n", encoding="utf-8")
    print(f"SEO: agenda.html con {total} eventos ({len(ld_eventos)} con datos estructurados) y sitemap.xml")


if __name__ == "__main__":
    main()
