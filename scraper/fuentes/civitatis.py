"""Civitatis: tours y full days desde Lima (van a lugares.json porque no tienen fecha fija).

Tarjetas: <a class="_activity-link"> con h3.comfort-card__title, nota '8,7 / 10', duración y precio.
El precio sale en la moneda que Civitatis elige según el país del visitante; se convierte a soles.
Consejo: Civitatis tiene programa de afiliados (te paga comisión y da un feed de actividades).
"""
import re

from comun import precio_de, redondear, sin_tildes

URL = "https://www.civitatis.com/es/lima/"
EXCLUIR = re.compile(r"traslado|transfer|shuttle|aeropuerto|airport", re.I)
FULL_DAY = re.compile(r"excursi|full ?day|paracas|huacachina|ballestas|\bica\b|nazca|lunahuan|"
                      r"pachacamac|caral|lachay|huancaya|canta|obrajillo|marcahuasi|antioquia", re.I)

JS = """
() => [...document.querySelectorAll('a._activity-link')].map(a => {
  const img = a.querySelector('img');
  const t = a.querySelector('.comfort-card__title');
  return {
    url: a.href,
    nombre: t ? t.innerText.trim() : (a.title || ''),
    imagen: img ? (img.dataset.src || img.src) : '',
    texto: a.innerText
  };
})
"""


def scrape(page, ctx):
    try:
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_selector("a._activity-link", timeout=25000)
    except Exception as e:
        print(f"  [civitatis] sin tarjetas ({e.__class__.__name__})")
        return []
    page.mouse.wheel(0, 20000)
    page.wait_for_timeout(1500)
    lugares, vistos = [], set()
    for t in page.evaluate(JS):
        url = t["url"].split("?")[0]
        if url in vistos or EXCLUIR.search(t["nombre"]):
            continue
        vistos.add(url)
        texto = t["texto"]
        texto_precio = re.sub(r"cancelaci[oó]n gratuita", " ", texto.replace("\n", " "), flags=re.I)
        precio = 0 if re.search(r"free tour", t["nombre"], re.I) else precio_de(texto_precio)
        if precio is None:
            continue
        nota = re.search(r"(\d+[,.]\d)\s*/\s*10", texto)
        horas = re.search(r"(\d+)\s*horas?", texto)
        es_full = bool(FULL_DAY.search(sin_tildes(t["nombre"]))) or (horas and int(horas.group(1)) >= 8)
        lugares.append({
            "nombre": t["nombre"],
            "lugar": "Desde Lima" if es_full else "Lima",
            "categoria": "Full day" if es_full else ("Free tour" if precio == 0 else "Tour"),
            "tipo": "aire" if es_full else "cultural",
            "precio": precio,
            "calificacion": redondear(float(nota.group(1).replace(",", ".")) / 2) if nota else None,
            "atributos": [],
            "imagen": t["imagen"],
            "url": url,
            "fuente": "Civitatis",
        })
    print(f"  [civitatis] {len(lugares)} actividades")
    return lugares
