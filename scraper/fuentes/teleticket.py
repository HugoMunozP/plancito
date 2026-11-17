"""Teleticket: tarjetas con imagen *calugalistado.jpg; si falta precio/fecha abre el detalle."""
import re

from comun import HOY, fechas_de, precio_de, scroll_hasta_el_final, sin_tildes

TELETICKET_URLS = [
    "https://teleticket.com.pe/",
    "https://teleticket.com.pe/todos",
    "https://teleticket.com.pe/musica",
    "https://teleticket.com.pe/teatro",
    "https://teleticket.com.pe/entretenimiento",
]


JS_TELETICKET = """
() => {
  const out = [];
  document.querySelectorAll('img[src*="calugalistado"], img[data-src*="calugalistado"]').forEach(img => {
    const a = img.closest('a') || img.closest('div')?.querySelector('a[href]');
    if (!a) return;
    let card = a;
    for (let i = 0; i < 4 && card.parentElement && card.innerText.trim().length < 15; i++) card = card.parentElement;
    out.push({
      url: a.href,
      nombre: img.alt || '',
      imagen: img.getAttribute('src') && !img.getAttribute('src').startsWith('data:') ? img.src : (img.dataset.src || img.src),
      texto: card.innerText
    });
  });
  return out;
}
"""


def categoria_teleticket(nombre, lugar, url):
    t = sin_tildes(f"{nombre} {url}".lower())
    if re.search(r"stand ?up|comedy|comedia|risoterapia|humor", t):
        return "Stand up"
    if re.search(r"tributo|concierto|tour|fest|en lima|sinfon|orquesta|salsa|rock|cumbia|criollo|gala", t):
        return "Concierto"
    if re.search(r"teatro|obra|musical|ballet|cascanueces", t + " " + sin_tildes(lugar.lower())):
        return "Teatro"
    return "Show"


def scrape(page, ctx):
    crudos = {}
    for url in TELETICKET_URLS:
        try:
            resp = page.goto(url, wait_until="domcontentloaded", timeout=60000)
            if resp and resp.status >= 400:
                continue
            page.wait_for_selector('img[src*="calugalistado"], img[data-src*="calugalistado"]', timeout=20000)
        except Exception:
            continue
        scroll_hasta_el_final(page, 'img[src*="calugalistado"], img[data-src*="calugalistado"]')
        for t in page.evaluate(JS_TELETICKET):
            if "teleticket.com.pe" in t["url"] and t["url"] not in crudos:
                crudos[t["url"]] = t
        print(f"  [teleticket] {url}: {len(crudos)} acumulados")

    eventos = []
    for u, t in crudos.items():
        lineas = [l.strip() for l in t["texto"].split("\n") if l.strip()]
        texto = " | ".join(lineas)
        f = fechas_de(texto)
        precio = precio_de(texto)
        lugar = next((l for l in lineas if " - " in l and "S/" not in l and not fechas_de(l)), "")
        # si la tarjeta no trae precio o fecha, se abre la página del evento
        if precio is None or not f or not lugar:
            try:
                page.goto(u, wait_until="domcontentloaded", timeout=45000)
                page.wait_for_timeout(2500)
                det = page.inner_text("body")
                precio = precio if precio is not None else precio_de(det)
                f = f or fechas_de(det[:3000])
                if not lugar:
                    lugar = next((l.strip() for l in det.split("\n") if " - " in l and "Lima" in l and len(l) < 120), "")
            except Exception:
                pass
        if not f or precio is None:
            continue
        nombre = t["nombre"].strip() or lineas[0]
        eventos.append({
            "nombre": nombre,
            "inicio": min(f).isoformat(),
            "fin": max(f).isoformat(),
            "hora": "",
            "lugar": lugar or "Lima",
            "categoria": categoria_teleticket(nombre, lugar, u),
            "tipo": "cultural",
            "precio": precio,
            "imagen": t["imagen"],
            "url": u,
            "fuente": "Teleticket",
        })
    print(f"  [teleticket] total: {len(eventos)} eventos")
    return eventos
