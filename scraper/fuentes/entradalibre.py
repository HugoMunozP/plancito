"""EntradaLibre: agenda HTML de eventos gratuitos (https://entradalibre.me/event/?pg=N).

Cada tarjeta es <article class="elini-ev"> con categoría, título, 'Mar, 17 nov · 10:00 a. m.' y distrito.
Cubre todo el Perú, así que se filtra a Lima Metropolitana y Callao.
"""
from bs4 import BeautifulSoup

from comun import es_de_lima, fechas_de, hora_de

BASE = "https://entradalibre.me/event/?pg={}"
MAX_PAGINAS = 30

CATEGORIAS = {
    "cine": ("Cine", "cine"),
    "concierto": ("Concierto", "cultural"),
    "musica": ("Concierto", "cultural"),
    "música": ("Concierto", "cultural"),
    "teatro": ("Teatro", "cultural"),
    "puesta en escena": ("Teatro", "cultural"),
    "danza": ("Danza", "cultural"),
    "exposición": ("Exposición", "cultural"),
    "exposicion": ("Exposición", "cultural"),
    "feria": ("Feria", "cultural"),
    "stand up": ("Stand up", "cultural"),
}


def scrape(page, ctx):
    eventos = {}
    for n in range(1, MAX_PAGINAS + 1):
        r = ctx.request.get(BASE.format(n), timeout=45000)
        if not r.ok:
            break
        sopa = BeautifulSoup(r.text(), "html.parser")
        nuevos = 0
        for art in sopa.select("article.elini-ev"):
            a = art.select_one("h3 a") or art.select_one("a[href]")
            if not a:
                continue
            url = a["href"].split("?")[0]
            if url in eventos:
                continue
            meta = art.select_one(".meta")
            lineas = [l.strip() for l in (meta.get_text("\n") if meta else "").split("\n") if l.strip()]
            fecha_txt = lineas[0] if lineas else ""
            distrito = lineas[-1] if len(lineas) > 1 else ""
            if not es_de_lima(distrito):
                continue
            f = fechas_de(fecha_txt)
            if not f:
                continue
            cat_txt = (art.select_one(".cat").get_text(strip=True) if art.select_one(".cat") else "Cultura")
            categoria, tipo = CATEGORIAS.get(cat_txt.lower(), (cat_txt.capitalize(), "cultural"))
            img = art.select_one("img")
            eventos[url] = {
                "nombre": a.get_text(" ", strip=True).title() if a.get_text().isupper() else a.get_text(" ", strip=True),
                "inicio": f[0].isoformat(),
                "fin": f[0].isoformat(),
                "hora": hora_de(fecha_txt),
                "lugar": distrito,
                "categoria": categoria,
                "tipo": tipo,
                "precio": 0,
                "imagen": img.get("src", "") if img else "",
                "url": url,
                "fuente": "EntradaLibre",
            }
            nuevos += 1
        print(f"  [entradalibre] página {n}: +{nuevos}")
        if nuevos == 0 and n > 1:
            break
    return list(eventos.values())
