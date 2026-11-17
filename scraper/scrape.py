"""
Plancito: genera data/eventos.json y data/lugares.json a partir de todas las fuentes.

Uso local:
    pip install -r requirements.txt
    python -m playwright install chromium
    python scraper/scrape.py            # eventos diarios (+ tours solo los lunes)
    FORZAR_TOURS=1 python scraper/scrape.py
"""
import json
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from playwright.sync_api import sync_playwright  # noqa: E402

from comun import HOY, LIMA, UA  # noqa: E402
from imagenes import bajar_todas  # noqa: E402
from fuentes import civitatis, entradalibre, eventbrite, formulario, google_places, incatrilogy, joinnus, teleticket  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
DATA = RAIZ / "data"
MANUAL = DATA / "manual"

# (nombre de la fuente tal como queda en el campo "fuente", módulo)
FUENTES_EVENTOS = [
    ("Joinnus", joinnus),
    ("Teleticket", teleticket),
    ("EntradaLibre", entradalibre),
    # ("Eventbrite", eventbrite),  # desactivado: muestra un captcha a los servidores de GitHub
    ("Formulario", formulario),
]
# Tours y full days cambian poco: se actualizan una vez por semana (lunes)
FUENTES_LUGARES = [
    ("Civitatis", civitatis),
    ("Inca Trilogy Tours", incatrilogy),
]
# Restaurantes, cafés y bares de Google Maps: casi no cambian. Solo se vuelven a consultar cuando
# lo pides (Actions > Run workflow > marcar "Volver a consultar Google Maps"). Si no, se reusan.
FUENTES_GOOGLE = [
    ("Google Maps", google_places),
]
MINIMO_EVENTOS = 15


def leer(ruta, clave):
    try:
        return json.loads(ruta.read_text(encoding="utf-8")).get(clave, [])
    except Exception:
        return []


def leer_lista(ruta):
    try:
        d = json.loads(ruta.read_text(encoding="utf-8"))
        return d if isinstance(d, list) else d.get("items", [])
    except Exception:
        return []


def correr(fuentes, page, ctx, anteriores):
    """Ejecuta cada fuente por separado. Si una falla o sale vacía, se reutiliza lo anterior."""
    total, resumen = [], {}
    for nombre, modulo in fuentes:
        print(f"{nombre}…")
        try:
            items = modulo.scrape(page, ctx)
        except Exception:
            traceback.print_exc()
            items = []
        if not items:
            items = [e for e in anteriores if e.get("fuente") == nombre]
            print(f"  AVISO: {nombre} sin resultados; se conservan {len(items)} anteriores.")
            resumen[nombre] = f"0 (reutilizados {len(items)})"
        else:
            resumen[nombre] = len(items)
        total += items
    return total, resumen


def main():
    eventos_ant = leer(DATA / "eventos.json", "eventos")
    lugares_ant = leer(DATA / "lugares.json", "lugares")

    # La primera vez, los lugares hechos a mano (sin "fuente") pasan a data/manual/lugares.json
    MANUAL.mkdir(parents=True, exist_ok=True)
    if not (MANUAL / "lugares.json").exists():
        a_mano = [l for l in lugares_ant if not l.get("fuente")]
        (MANUAL / "lugares.json").write_text(json.dumps(a_mano, ensure_ascii=False, indent=1), encoding="utf-8")
    if not (MANUAL / "eventos.json").exists():
        (MANUAL / "eventos.json").write_text("[]\n", encoding="utf-8")

    previos_tours = [l for l in lugares_ant if l.get("fuente") in dict(FUENTES_LUGARES)]
    previos_google = [l for l in lugares_ant if l.get("fuente") in dict(FUENTES_GOOGLE)]
    hacer_tours = HOY.weekday() == 0 or os.environ.get("FORZAR_TOURS") == "1" or not previos_tours
    hacer_google = os.environ.get("FORZAR_GOOGLE") == "1" or not previos_google

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(locale="es-PE", timezone_id="America/Lima",
                                  viewport={"width": 1366, "height": 900}, user_agent=UA)
        page = ctx.new_page()
        eventos, res_ev = correr(FUENTES_EVENTOS, page, ctx, eventos_ant)
        if hacer_tours:
            tours, res_lu = correr(FUENTES_LUGARES, page, ctx, lugares_ant)
        else:
            tours = previos_tours
            res_lu = {"(tours)": f"sin cambios hasta el lunes ({len(tours)})"}
        if hacer_google:
            google, res_g = correr(FUENTES_GOOGLE, page, ctx, lugares_ant)
        else:
            google = previos_google
            res_g = {"Google Maps": f"sin consultar, se reusan {len(google)}"}
        tours = tours + google
        res_lu.update(res_g)
        browser.close()

    # ---- eventos (los manuales de data/manual/ los lee la web directamente, desde admin.html)
    vistos, limpios = set(), []
    for e in eventos:
        clave = e.get("url") or (e.get("nombre", "").lower(), e.get("inicio"))
        if clave in vistos or not e.get("fin") or e["fin"] < HOY.isoformat():
            continue
        vistos.add(clave)
        limpios.append(e)
    limpios.sort(key=lambda e: (e["inicio"], e["nombre"].lower()))

    if len(limpios) < MINIMO_EVENTOS:
        print(f"ERROR: solo {len(limpios)} eventos; no se sobrescribe nada.")
        sys.exit(1)

    ahora = datetime.now(LIMA).strftime("%Y-%m-%dT%H:%M-05:00")
    (DATA / "eventos.json").write_text(
        json.dumps({"actualizado": ahora, "eventos": limpios}, ensure_ascii=False, indent=1), encoding="utf-8")

    # ---- lugares: solo los automáticos (los manuales los lee la web desde data/manual/lugares.json)
    vistos_l, lugares = set(), []
    for t in tours:
        if t.get("url") and t["url"] not in vistos_l:
            vistos_l.add(t["url"])
            lugares.append(t)
    # ---- fotos: se bajan a img/cache/ para no depender de otras páginas
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(user_agent=UA)
        bajar_todas(ctx, limpios + lugares, RAIZ / "img" / "cache", RAIZ)
        browser.close()
    (DATA / "eventos.json").write_text(
        json.dumps({"actualizado": ahora, "eventos": limpios}, ensure_ascii=False, indent=1), encoding="utf-8")
    (DATA / "lugares.json").write_text(
        json.dumps({"actualizado": ahora, "lugares": lugares}, ensure_ascii=False, indent=1), encoding="utf-8")

    print("\nResumen:")
    for k, v in {**res_ev, **res_lu}.items():
        print(f"  {k:20} {v}")
    print(f"OK: {len(limpios)} eventos y {len(lugares)} lugares guardados.")


if __name__ == "__main__":
    main()
