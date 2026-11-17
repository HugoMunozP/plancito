"""Inca Trilogy Tours: full days desde Lima vía su API pública de WordPress (/wp-json/wp/v2/tour).

Categorías usadas: 833 Full Days en Lima, 546 Excursiones en Lima, 589 Free tours en Lima,
542 Lunahuaná, 743 Pachacamac. Los precios están en dólares (campo precio_adulto) y se pasan a soles.
"""
import html

from comun import a_soles

API = ("https://www.incatrilogytours.com/wp-json/wp/v2/tour?per_page=100&page={}&tour-category={}"
       "&_fields=title,link,precio,precio_adulto,duracion,dias,salidas,lang,tour-category,yoast_head_json.og_image")
CATEGORIAS = {833: "Full day", 546: "Tour", 589: "Free tour", 542: "Full day", 743: "Tour"}


def _num(v):
    try:
        return float(str(v).replace(",", ""))
    except (TypeError, ValueError):
        return 0.0


def scrape(page, ctx):
    lugares = {}
    for cat_id, categoria in CATEGORIAS.items():
        for n in range(1, 5):
            r = ctx.request.get(API.format(n, cat_id), timeout=45000)
            if not r.ok:
                break
            datos = r.json()
            if not datos:
                break
            for t in datos:
                if t.get("lang", "es") != "es" or t["link"] in lugares:
                    continue
                dur = (t.get("duracion") or "").lower()
                if "noche" in dur or ("día" in dur and not dur.startswith("1")):
                    continue  # solo planes de un día
                usd = _num(t.get("precio_adulto")) or _num(t.get("precio"))
                if usd == 0 and categoria != "Free tour":
                    continue
                img = ((t.get("yoast_head_json") or {}).get("og_image") or [{}])[0].get("url", "")
                lugares[t["link"]] = {
                    "nombre": html.unescape(t["title"]["rendered"]),
                    "lugar": "Desde Lima",
                    "categoria": categoria,
                    "tipo": "aire" if categoria == "Full day" else "cultural",
                    "precio": a_soles(usd, "USD"),
                    "calificacion": None,
                    "atributos": [],
                    "salidas": t.get("salidas") or "",
                    "imagen": img,
                    "url": t["link"],
                    "fuente": "Inca Trilogy Tours",
                }
            if len(datos) < 100:
                break
    print(f"  [incatrilogy] {len(lugares)} tours")
    return list(lugares.values())
