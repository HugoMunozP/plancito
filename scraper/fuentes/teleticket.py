"""Teleticket: lista completa en https://teleticket.com.pe/todos (HTML del servidor).

Cada tarjeta:
  <a href=".../evento/...">
    <img src="...calugalistado.jpg">
    <p class="descripcion"><strong>LOCAL - DISTRITO - LIMA</strong> / Categoría</p>
    <h3 title="NOMBRE">NOMBRE</h3>
    <p class="fecha">17 de noviembre 2026 - 22 de noviembre 2026</p>
  </a>
El precio no está en la lista: se toma el más bajo de la página del evento (sin tarifas CONADIS).
"""
import re

from bs4 import BeautifulSoup

from comun import es_de_lima, fechas_de, redondear, sin_tildes

LISTA = "https://teleticket.com.pe/todos"

CATEGORIAS = {
    "musica": "Concierto", "humor": "Stand up", "stand up": "Stand up", "teatro": "Teatro",
    "circo": "Show", "entretencion": "Show", "familia": "Show", "danza": "Danza",
    "deportes": "Deporte", "festival": "Festival", "festivales": "Festival",
}


def capitalizar(t):
    """'LIMA COMEDY CLUB - MIRAFLORES - LIMA' -> 'Lima Comedy Club - Miraflores - Lima' (por tramos)."""
    def tramo(x):
        return " ".join(p.capitalize() if len(p) > 2 else p.lower() for p in x.split()) if x.isupper() else x
    return " - ".join(tramo(x.strip()) for x in t.split(" - "))


def precio_detalle(ctx, url):
    try:
        r = ctx.request.get(url, timeout=30000)
        if not r.ok:
            return None
        sopa = BeautifulSoup(r.text(), "html.parser")
        for s in sopa(["script", "style"]):
            s.decompose()
        texto = re.sub(r"\s+", " ", sopa.get_text(" "))
    except Exception:
        return None
    vals, fin_anterior = [], 0
    for m in re.finditer(r"S/\.?\s?(\d[\d,]*(?:\.\d{1,2})?)", texto):
        antes = texto[max(fin_anterior, m.start() - 40):m.start()].upper()
        fin_anterior = m.end()
        if "CONADIS" in antes:
            continue
        try:
            v = float(m.group(1).replace(",", ""))
        except ValueError:
            continue
        if v > 0:
            vals.append(v)
    return redondear(min(vals)) if vals else None


def scrape(page, ctx):
    r = ctx.request.get(LISTA, timeout=60000)
    if not r.ok:
        print(f"  [teleticket] HTTP {r.status}")
        return []
    sopa = BeautifulSoup(r.text(), "html.parser")
    eventos, vistos = [], set()
    tarjetas = [a for a in sopa.select("a[href]") if a.select_one("p.descripcion") and a.select_one("h3")]
    for a in tarjetas:
        url = a["href"]
        if url in vistos:
            continue
        vistos.add(url)
        desc = a.select_one("p.descripcion")
        local = desc.select_one("strong").get_text(" ", strip=True) if desc.select_one("strong") else ""
        cat_txt = desc.get_text(" ", strip=True).split("/")[-1].strip() if "/" in desc.get_text() else ""
        if not es_de_lima(local):
            continue
        h3 = a.select_one("h3")
        nombre = (h3.get("title") or h3.get_text(" ", strip=True)).strip()
        f = fechas_de(a.select_one("p.fecha").get_text(" ", strip=True) if a.select_one("p.fecha") else "")
        if not f or not nombre:
            continue
        precio = precio_detalle(ctx, url)
        if precio is None:
            continue
        img = a.select_one("img")
        categoria = CATEGORIAS.get(sin_tildes(cat_txt.lower()), capitalizar(cat_txt) or "Show")
        eventos.append({
            "nombre": capitalizar(nombre),
            "inicio": min(f).isoformat(),
            "fin": max(f).isoformat(),
            "hora": "",
            "lugar": capitalizar(local),
            "categoria": categoria,
            "tipo": "aire" if categoria == "Deporte" else "cultural",
            "precio": precio,
            "imagen": img.get("src", "") if img else "",
            "url": url,
            "fuente": "Teleticket",
        })
    print(f"  [teleticket] {len(tarjetas)} tarjetas, {len(eventos)} en Lima con precio")
    return eventos
