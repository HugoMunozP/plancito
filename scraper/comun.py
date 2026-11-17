"""Funciones compartidas por todas las fuentes."""
import re
import unicodedata
from datetime import date, datetime, timedelta, timezone

LIMA = timezone(timedelta(hours=-5))
HOY = datetime.now(LIMA).date()

# Tipo de cambio para convertir precios en dólares/euros a soles.
# Ajústalo de vez en cuando (o cámbialo por una consulta a una API de tipo de cambio).
TIPO_CAMBIO = {"USD": 3.75, "EUR": 4.05, "PEN": 1.0}

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/130.0 Safari/537.36")

MESES = {
    "ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6, "jul": 7,
    "ago": 8, "set": 9, "sep": 9, "oct": 10, "nov": 11, "dic": 12,
}

# Lima Metropolitana + Callao (para filtrar fuentes de todo el Perú)
DISTRITOS_LIMA = {
    "lima", "cercado de lima", "ancon", "ate", "barranco", "brena", "carabayllo", "chaclacayo",
    "chorrillos", "cieneguilla", "comas", "el agustino", "independencia", "jesus maria",
    "la molina", "la victoria", "lince", "los olivos", "lurigancho", "chosica", "lurin",
    "magdalena del mar", "magdalena", "miraflores", "pachacamac", "pucusana", "pueblo libre",
    "puente piedra", "punta hermosa", "punta negra", "rimac", "san bartolo", "san borja",
    "san isidro", "san juan de lurigancho", "san juan de miraflores", "san luis",
    "san martin de porres", "san miguel", "santa anita", "santa maria del mar", "santa rosa",
    "santiago de surco", "surco", "surquillo", "villa el salvador", "villa maria del triunfo",
    "callao", "bellavista", "carmen de la legua", "la perla", "la punta", "ventanilla", "mi peru",
}


# Nombres para mostrar (el filtro de zona de la web usa la misma lista)
DISTRITOS_NOMBRES = [
    "Ancón", "Ate", "Barranco", "Bellavista", "Breña", "Callao", "Carabayllo", "Carmen de la Legua", "Cercado de Lima",
    "Chaclacayo", "Chorrillos", "Cieneguilla", "Comas", "El Agustino", "Independencia", "Jesús María", "La Molina",
    "La Perla", "La Punta", "La Victoria", "Lince", "Los Olivos", "Lurigancho", "Lurín", "Magdalena del Mar",
    "Miraflores", "Pachacámac", "Pucusana", "Pueblo Libre", "Puente Piedra", "Punta Hermosa", "Punta Negra", "Rímac",
    "San Bartolo", "San Borja", "San Isidro", "San Juan de Lurigancho", "San Juan de Miraflores", "San Luis",
    "San Martín de Porres", "San Miguel", "Santa Anita", "Santa María del Mar", "Santa Rosa", "Santiago de Surco",
    "Surquillo", "Ventanilla", "Villa El Salvador", "Villa María del Triunfo",
]
ALIAS_DISTRITO = {"surco": "Santiago de Surco", "cercado": "Cercado de Lima", "magdalena": "Magdalena del Mar", "smp": "San Martín de Porres"}


def distrito_de(texto):
    """Distrito de Lima mencionado en un texto (dirección o lugar), o '' si no hay."""
    t = " " + re.sub(r"[^a-z0-9]+", " ", sin_tildes((texto or "").lower())) + " "
    for d in sorted(DISTRITOS_NOMBRES, key=len, reverse=True):
        if " " + re.sub(r"[^a-z0-9]+", " ", sin_tildes(d.lower())) + " " in t:
            return d
    for a, d in ALIAS_DISTRITO.items():
        if f" {a} " in t:
            return d
    return ""


def sin_tildes(t):
    return "".join(c for c in unicodedata.normalize("NFD", t or "") if unicodedata.category(c) != "Mn")


def es_de_lima(lugar):
    t = sin_tildes((lugar or "").lower())
    return any(re.search(rf"\b{re.escape(d)}\b", t) for d in DISTRITOS_LIMA)


def redondear(v):
    v = round(float(v), 2)
    return int(v) if v == int(v) else v


def a_soles(monto, moneda="PEN"):
    return redondear(float(monto) * TIPO_CAMBIO.get(moneda, 1.0))


def precio_de(texto):
    """Busca el precio más bajo en un texto. Entiende S/, US$, USD, $ y €. Devuelve soles."""
    if not texto:
        return None
    texto = re.sub(r"cancelaci[oó]n gratuita|ingreso libre a|libro de reclamaciones", " ", texto, flags=re.I)
    if re.search(r"\b(gratis|gratuito|entrada libre|ingreso libre|free)\b", texto, re.I):
        return 0
    patrones = [
        (r"S/\.?\s*([\d.,]+)", "PEN"), (r"([\d.,]+)\s*S/", "PEN"),
        (r"(?:US\$|USD)\s*([\d.,]+)", "USD"), (r"([\d.,]+)\s*(?:US\$|USD)", "USD"),
        (r"€\s*([\d.,]+)", "EUR"), (r"([\d.,]+)\s*€", "EUR"),
    ]
    vals = []
    for pat, moneda in patrones:
        for n in re.findall(pat, texto):
            n = n.strip(".,")
            # 1.234,50 -> 1234.50 ; 1,234.50 -> 1234.50
            if re.search(r",\d{1,2}$", n):
                n = n.replace(".", "").replace(",", ".")
            else:
                n = n.replace(",", "")
            try:
                vals.append(float(n) * TIPO_CAMBIO[moneda])
            except ValueError:
                pass
    return redondear(min(vals)) if vals else None


def anio_probable(mes, anio=None):
    if anio:
        return anio
    return HOY.year + 1 if mes < HOY.month - 1 else HOY.year


def fechas_de(texto):
    """Fechas tipo '17 nov', "21 NOV '26", '5 de diciembre de 2026', '19 | Nov'."""
    t = sin_tildes((texto or "").lower())
    res = []
    for d, m, a2, a4 in re.findall(
            r"(\d{1,2})[\s|]*(?:de\s+)?([a-z]{3})[a-z]*\.?[\s|]*(?:'(\d{2})|(?:de\s+)?(\d{4}))?", t):
        if m not in MESES:
            continue
        anio = int(a2) + 2000 if a2 else (int(a4) if a4 else None)
        try:
            res.append(date(anio_probable(MESES[m], anio), MESES[m], int(d)))
        except ValueError:
            pass
    return res


def hora_de(texto):
    """'10:00 a. m.' -> '10:00 am' ; '19:30' -> '7:30 pm'."""
    t = (texto or "").lower()
    m = re.search(r"(\d{1,2}):(\d{2})\s*([ap])\.?\s*m\.?", t)
    if m:
        return f"{int(m.group(1))}:{m.group(2)} {m.group(3)}m"
    m = re.search(r"\b(\d{1,2}):(\d{2})\b", t)
    if m:
        h = int(m.group(1))
        return f"{(h - 1) % 12 + 1}:{m.group(2)} {'pm' if h >= 12 else 'am'}"
    return ""


def scroll_hasta_el_final(page, selector, max_vueltas=15):
    previo = -1
    for _ in range(max_vueltas):
        n = page.locator(selector).count()
        if n == previo:
            break
        previo = n
        page.mouse.wheel(0, 20000)
        page.wait_for_timeout(1500)
        boton = page.get_by_role("button", name=re.compile(r"ver m[aá]s|cargar m[aá]s", re.I))
        if boton.count():
            try:
                boton.first.click(timeout=2000)
                page.wait_for_timeout(1500)
            except Exception:
                pass
