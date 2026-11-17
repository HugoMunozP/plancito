"""Restaurantes, cafés y bares mejor calificados de Google Maps, vía la API oficial de Google Places (New).

Distritos: Miraflores, San Isidro, San Borja y Santiago de Surco.

Requisitos:
  - Una API key de Google Cloud con "Places API (New)" activada, guardada en GitHub como
    secreto GOOGLE_PLACES_API_KEY (Settings > Secrets and variables > Actions > Secrets).

Costo: cada página de resultados (hasta 20 lugares) es 1 llamada "Text Search Enterprise + Atmosphere".
Google da 1.000 llamadas gratis al mes por SKU. Aquí se hacen como máximo
(2 + 2 + 1 búsquedas) x 4 distritos x 3 páginas = 60 llamadas por corrida, 1 vez por semana (~260 al mes).
No se piden fotos: cada foto mostrada en la web se cobraría aparte.

Ojo con los términos de Google Maps Platform: limitan guardar ("cachear") datos de Places.
Por eso se refresca cada semana y la web muestra la atribución "Datos de Google Maps".
"""
import os

from comun import redondear, sin_tildes

URL = "https://places.googleapis.com/v1/places:searchText"
DISTRITOS = {  # nombre a mostrar: texto que debe aparecer en la dirección
    "Miraflores": "miraflores",
    "San Isidro": "san isidro",
    "San Borja": "san borja",
    "Santiago de Surco": "surco",
}
NOTA_MINIMA = 4.5
# Qué se busca en Google Maps. Cada búsqueda trae hasta 60 lugares (3 páginas = 3 llamadas).
TIPOS = [
    {"tipo_google": "restaurant", "categoria": "Restaurante", "tipo": "restaurantes",
     "busquedas": ["restaurantes en {}, Lima, Perú", "mejores restaurantes en {}, Lima"],
     "resenas_min": 150, "por_distrito": 25, "precio_defecto": None,
     "precios": {"PRICE_LEVEL_INEXPENSIVE": 25, "PRICE_LEVEL_MODERATE": 50,
                 "PRICE_LEVEL_EXPENSIVE": 100, "PRICE_LEVEL_VERY_EXPENSIVE": 180}},
    {"tipo_google": "cafe", "categoria": "Café", "tipo": "cafe",
     "busquedas": ["cafeterías en {}, Lima, Perú", "café de especialidad en {}, Lima"],
     "resenas_min": 80, "por_distrito": 20, "precio_defecto": 25,
     "precios": {"PRICE_LEVEL_INEXPENSIVE": 15, "PRICE_LEVEL_MODERATE": 25,
                 "PRICE_LEVEL_EXPENSIVE": 45, "PRICE_LEVEL_VERY_EXPENSIVE": 70}},
    {"tipo_google": "bar", "categoria": "Bar", "tipo": "bar",
     "busquedas": ["bares en {}, Lima, Perú"],
     "resenas_min": 100, "por_distrito": 15, "precio_defecto": 45,
     "precios": {"PRICE_LEVEL_INEXPENSIVE": 25, "PRICE_LEVEL_MODERATE": 45,
                 "PRICE_LEVEL_EXPENSIVE": 80, "PRICE_LEVEL_VERY_EXPENSIVE": 130}},
]

CAMPOS = ",".join([
    "places.id", "places.displayName", "places.formattedAddress", "places.rating", "places.userRatingCount",
    "places.priceLevel", "places.priceRange", "places.googleMapsUri", "places.types",
    "places.primaryTypeDisplayName", "places.outdoorSeating", "places.servesVegetarianFood",
    "places.goodForChildren", "places.allowsDogs", "places.liveMusic", "places.servesDessert",
    "places.servesCocktails", "nextPageToken",
])



def puntaje(nota, resenas, m=300, media=4.3):
    """Promedio bayesiano: premia nota alta CON muchas reseñas (un 5.0 con 8 reseñas no gana)."""
    return (resenas * nota + m * media) / (resenas + m)


def precio_persona(p, conf):
    rango = p.get("priceRange") or {}
    ini = (rango.get("startPrice") or {})
    fin = (rango.get("endPrice") or {})
    if ini.get("currencyCode") == "PEN" and ini.get("units"):
        a = float(ini["units"])
        b = float(fin["units"]) if fin.get("units") else a * 1.4
        return redondear(round((a + b) / 2))
    return conf["precios"].get(p.get("priceLevel"), conf["precio_defecto"])


def atributos(p):
    a = []
    if p.get("outdoorSeating"):
        a.append("terraza")
    if p.get("servesVegetarianFood"):
        a.append("vegetariano")
    if p.get("goodForChildren"):
        a.append("ninos")
    if p.get("allowsDogs"):
        a.append("pet")
    if p.get("liveMusic"):
        a.append("musica")
    if p.get("servesDessert"):
        a.append("postres")
    if p.get("servesCocktails") and "bar" in (p.get("types") or []):
        a.append("happy")
    tipos = set(p.get("types") or [])
    if tipos & {"fine_dining_restaurant", "wine_bar"} or p.get("priceLevel") in (
            "PRICE_LEVEL_EXPENSIVE", "PRICE_LEVEL_VERY_EXPENSIVE"):
        a.append("romantico")
    return a


def scrape(page, ctx):
    clave = os.environ.get("GOOGLE_PLACES_API_KEY", "").strip()
    if not clave:
        print("  [google] sin GOOGLE_PLACES_API_KEY, se omite")
        return []
    cabeceras = {"Content-Type": "application/json", "X-Goog-Api-Key": clave, "X-Goog-FieldMask": CAMPOS}
    resultado, ya = [], set()  # ya: ids usados (un lugar sale una sola vez aunque sea café y bar)
    for conf in TIPOS:
        for distrito, clave_dir in DISTRITOS.items():
            vistos = {}
            for busqueda in conf["busquedas"]:
                token = None
                for _ in range(3):  # hasta 60 resultados por búsqueda
                    cuerpo = {"textQuery": busqueda.format(distrito), "languageCode": "es", "regionCode": "PE",
                              "includedType": conf["tipo_google"], "minRating": NOTA_MINIMA, "pageSize": 20}
                    if token:
                        cuerpo["pageToken"] = token
                    r = ctx.request.post(URL, headers=cabeceras, data=cuerpo, timeout=30000)
                    if not r.ok:
                        print(f"  [google] {conf['categoria']} {distrito}: HTTP {r.status} {r.text()[:200]}")
                        break
                    datos = r.json()
                    for p in datos.get("places", []):
                        if p["id"] in vistos or p["id"] in ya:
                            continue
                        if clave_dir not in sin_tildes((p.get("formattedAddress") or "").lower()):
                            continue
                        nota, resenas = p.get("rating") or 0, p.get("userRatingCount") or 0
                        precio = precio_persona(p, conf)
                        if nota < NOTA_MINIMA or resenas < conf["resenas_min"] or precio is None:
                            continue
                        vistos[p["id"]] = (puntaje(nota, resenas), {
                            "nombre": (p.get("displayName") or {}).get("text", ""),
                            "lugar": distrito,
                            "categoria": conf["categoria"],
                            "tipo": conf["tipo"],
                            "precio": precio,
                            "calificacion": round(nota, 1),
                            "resenas": resenas,
                            "atributos": atributos(p),
                            "subtipo": (p.get("primaryTypeDisplayName") or {}).get("text", ""),
                            "url": p.get("googleMapsUri", ""),
                            "fuente": "Google Maps",
                        })
                    token = datos.get("nextPageToken")
                    if not token:
                        break
            mejores = sorted(vistos.items(), key=lambda x: -x[1][0])[:conf["por_distrito"]]
            ya.update(k for k, _ in mejores)
            resultado += [v[1] for _, v in mejores]
            print(f"  [google] {conf['categoria']} {distrito}: {len(vistos)} candidatos, se quedan {len(mejores)}")
    return resultado
