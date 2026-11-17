"""Eventbrite: eventos gratuitos en Lima.

Ojo: Eventbrite cerró en 2020 la búsqueda pública de su API (/events/search), así que la API
oficial solo sirve para eventos de organizadores que tú administras. Aquí se lee el JSON-LD
(schema.org/Event) que la propia página de resultados publica.
"""
import json
import re

from comun import es_de_lima, hora_de, sin_tildes

URL = "https://www.eventbrite.com.pe/d/peru--lima/free--events/?page={}"
MAX_PAGINAS = 5


def categoria(nombre):
    t = sin_tildes(nombre.lower())
    if re.search(r"concierto|music|jazz|rock|coro|recital", t):
        return "Concierto"
    if re.search(r"taller|workshop|clase|curso", t):
        return "Taller"
    if re.search(r"feria|bazar|mercado", t):
        return "Feria"
    if re.search(r"yoga|run|carrera|deporte|futbol|padel|surf", t):
        return "Deporte"
    return "Charla"


def scrape(page, ctx):
    eventos = {}
    for n in range(1, MAX_PAGINAS + 1):
        try:
            page.goto(URL.format(n), wait_until="domcontentloaded", timeout=60000)
            try:
                page.wait_for_selector('script[type="application/ld+json"]', state="attached", timeout=15000)
            except Exception:
                pass
        except Exception:
            break
        bloques = page.eval_on_selector_all(
            'script[type="application/ld+json"]', "els => els.map(e => e.textContent)")
        items = []
        for b in bloques:
            try:
                j = json.loads(b)
            except ValueError:
                continue
            for x in (j if isinstance(j, list) else [j]):
                items += [i.get("item", {}) for i in x.get("itemListElement", []) if isinstance(i, dict)]
        nuevos = 0
        for ev in items:
            if ev.get("@type") != "Event" or not ev.get("url") or ev["url"] in eventos:
                continue
            if "Online" in ev.get("eventAttendanceMode", ""):
                continue
            loc = ev.get("location") or {}
            adr = loc.get("address") or {}
            lugar = adr.get("addressLocality") or "Lima"
            if not es_de_lima(f"{lugar} {adr.get('addressRegion', '')}"):
                continue
            ini, fin = ev.get("startDate", ""), ev.get("endDate") or ev.get("startDate", "")
            if not ini:
                continue
            eventos[ev["url"]] = {
                "nombre": ev.get("name", "").strip(),
                "inicio": ini[:10],
                "fin": fin[:10],
                "hora": hora_de(ini[11:16]) if "T" in ini else "",
                "lugar": f"{loc.get('name')} - {lugar}" if loc.get("name") else lugar,
                "categoria": categoria(ev.get("name", "")),
                "tipo": "aire" if categoria(ev.get("name", "")) == "Deporte" else "cultural",
                "precio": 0,
                "imagen": ev.get("image", ""),
                "url": ev["url"],
                "fuente": "Eventbrite",
            }
            nuevos += 1
        print(f"  [eventbrite] página {n}: +{nuevos} (título: {page.title()[:60]!r}, json-ld: {len(bloques)})")
        if not items:
            break
    return list(eventos.values())
