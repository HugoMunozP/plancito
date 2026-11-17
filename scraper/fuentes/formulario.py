"""Formulario de Google: para lo que no se puede scrapear.

Sirve para agencias de full days que solo publican en Facebook o Instagram, eventos de las
municipalidades, clubes de pádel, escuelas de stand-up paddle y centros culturales.

1. Crea un Google Form con estas preguntas (los nombres deben ser iguales):
   nombre, fecha_inicio (AAAA-MM-DD), fecha_fin, hora, lugar, categoria, precio, url, imagen
2. Abre la hoja de respuestas y agrega a mano una columna 'aprobado'. Solo entra lo que tenga 'si'.
3. En la hoja: Archivo > Compartir > Publicar en la web > la hoja de respuestas > CSV. Copia el enlace.
4. En GitHub: Settings > Secrets and variables > Actions > Variables > New variable
   Nombre: FORM_CSV_URL   Valor: el enlace del paso 3.
"""
import csv
import io
import os

from comun import precio_de

TIPOS = {"full day": "aire", "paseo": "aire", "deporte": "aire", "padel": "aire", "pádel": "aire",
         "paddle": "aire", "cine": "cine", "fiesta": "bar", "bar": "bar", "comida": "restaurantes"}


def scrape(page, ctx):
    url = os.environ.get("FORM_CSV_URL", "").strip()
    if not url:
        print("  [formulario] sin FORM_CSV_URL, se omite")
        return []
    r = ctx.request.get(url, timeout=30000)
    if not r.ok:
        return []
    eventos = []
    for fila in csv.DictReader(io.StringIO(r.text())):
        f = {k.strip().lower(): (v or "").strip() for k, v in fila.items() if k}
        if f.get("aprobado", "").lower() not in ("si", "sí", "x", "1"):
            continue
        precio = precio_de(f.get("precio", "")) if not f.get("precio", "").replace(".", "").isdigit() \
            else float(f["precio"])
        if not f.get("nombre") or not f.get("fecha_inicio") or precio is None:
            continue
        cat = f.get("categoria") or "Evento"
        eventos.append({
            "nombre": f["nombre"],
            "inicio": f["fecha_inicio"][:10],
            "fin": (f.get("fecha_fin") or f["fecha_inicio"])[:10],
            "hora": f.get("hora", ""),
            "lugar": f.get("lugar") or "Lima",
            "categoria": cat,
            "tipo": TIPOS.get(cat.lower(), "cultural"),
            "precio": int(precio) if precio == int(precio) else precio,
            "imagen": f.get("imagen", ""),
            "url": f.get("url", ""),
            "fuente": "Formulario",
        })
    print(f"  [formulario] {len(eventos)} eventos aprobados")
    return eventos
