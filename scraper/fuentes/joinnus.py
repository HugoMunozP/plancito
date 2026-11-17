"""Joinnus: tarjetas renderizadas con JavaScript en /descubrir/<categoria>."""
import re

import json

from comun import HOY, distrito_de, fechas_de, precio_de, scroll_hasta_el_final, sin_tildes

JOINNUS_CATEGORIAS = {
    # slug en joinnus: (categoria, tipo)
    "concerts": ("Concierto", "cultural"),
    "theater": ("Teatro", "cultural"),
    "stand-up": ("Stand up", "cultural"),
    "entertainment": ("Show", "cultural"),
    "art-culture": ("Cultura", "cultural"),
    "festivales": ("Festival", "cultural"),
    "party": ("Fiesta", "bar"),
    "cine": ("Cine", "cine"),
    "sports": ("Deporte", "aire"),
    "futbol": ("Fútbol", "aire"),
    "trip-adventure": ("Paseo", "aire"),
    "food-drinks": ("Comida", "restaurantes"),
}
JOINNUS_CIUDADES = ("lima-", "callao-")

JS_JOINNUS = """
() => [...document.querySelectorAll('[data-cy$="event--card"]')].map(c => {
  const a = c.querySelector('a[href*="/events/"]');
  const img = c.querySelector('img');
  return {
    url: a ? a.href : null,
    nombre: img ? img.alt : '',
    imagen: img ? (img.currentSrc || img.src) : '',
    hora: c.getAttribute('formatted-time') || '',
    texto: c.innerText
  };
})
"""


def scrape(page, ctx):
    eventos = {}
    for slug, (categoria, tipo) in JOINNUS_CATEGORIAS.items():
        url = f"https://www.joinnus.com/descubrir/{slug}"
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_selector('[data-cy$="event--card"]', timeout=25000)
        except Exception as e:
            print(f"  [joinnus] {slug}: sin tarjetas ({e.__class__.__name__})")
            continue
        scroll_hasta_el_final(page, '[data-cy$="event--card"]')
        tarjetas = page.evaluate(JS_JOINNUS)
        nuevos = 0
        for t in tarjetas:
            u = t["url"]
            if not u or u in eventos:
                continue
            partes = u.split("/events/")[-1].split("/")
            if len(partes) < 2 or not partes[1].startswith(JOINNUS_CIUDADES):
                continue  # solo Lima y Callao
            cat, tip = JOINNUS_CATEGORIAS.get(partes[0], (categoria, tipo))
            lineas = [l.strip() for l in t["texto"].split("\n") if l.strip()]
            f = fechas_de(" ".join(lineas[:3]))
            precio = precio_de(t["texto"])
            if not f or precio is None:
                continue
            ciudad = "Callao" if partes[1].startswith("callao-") else "Lima"
            nombre = t["nombre"].strip() or next((l for l in lineas[4:] if "S/" not in l), "")
            eventos[u] = {
                "nombre": nombre,
                "inicio": f[0].isoformat(),
                "fin": f[0].isoformat(),
                "hora": t["hora"],
                "lugar": ciudad,
                "categoria": cat,
                "tipo": tip,
                "precio": precio,
                "imagen": t["imagen"],
                "url": u,
                "fuente": "Joinnus",
            }
            nuevos += 1
        print(f"  [joinnus] {slug}: {nuevos} eventos")
    completar_lugares(ctx, eventos)
    return list(eventos.values())


def completar_lugares(ctx, eventos):
    """La tarjeta solo dice «Lima». La página del evento trae el local y la dirección (JSON-LD):
    se usan para poner «Local - Distrito» y que funcione el filtro por zona."""
    n = 0
    for u, e in eventos.items():
        try:
            r = ctx.request.get(u, timeout=20000)
            if not r.ok:
                continue
            for bloque in re.findall(r'<script type="application/ld\+json"[^>]*>([\s\S]*?)</script>', r.text()):
                try:
                    d = json.loads(bloque)
                except ValueError:
                    continue
                loc = d.get("location") if isinstance(d, dict) else None
                if not isinstance(loc, dict):
                    continue
                adr = loc.get("address") or {}
                dist = distrito_de(adr.get("streetAddress", "") if isinstance(adr, dict) else str(adr))
                local = (loc.get("name") or "").strip()
                if dist:
                    e["lugar"] = (local.title() + " - " + dist) if local else dist
                    n += 1
                break
        except Exception:
            continue
    print(f"  [joinnus] distrito encontrado en {n} de {len(eventos)} eventos")

