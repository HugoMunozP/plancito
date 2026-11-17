"""Descarga las fotos de eventos y lugares a img/cache/ (reducidas a 640 px, WebP).

Así la web no depende de las imágenes de otras páginas (que pueden cambiar, bloquear o tardar)
y la vista previa en Claude, que no puede cargar imágenes externas, también las muestra.
Cada item guarda la ruta local en "imagen_local". Las fotos que ya nadie usa se borran.
"""
import hashlib
import io
import os
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image

ANCHO = 640
CALIDAD = 70


def _nombre(url):
    return hashlib.sha1(url.encode("utf-8")).hexdigest()[:16] + ".webp"


def _guardar(datos, archivo):
    img = Image.open(io.BytesIO(datos)).convert("RGB")
    if img.width > ANCHO:
        img = img.resize((ANCHO, round(img.height * ANCHO / img.width)), Image.LANCZOS)
    img.save(archivo, "WEBP", quality=CALIDAD, method=6)


def _foto_google(ctx, it, carpeta):
    """Foto de Google Maps (API Place Photos). Se baja UNA vez por lugar: si ya existe no se vuelve a pedir
    (cada descarga cuenta como una consulta; Google da 1.000 gratis al mes)."""
    clave = os.environ.get("GOOGLE_PLACES_API_KEY", "").strip()
    archivo = carpeta / ("g-" + hashlib.sha1(it["place_id"].encode()).hexdigest()[:16] + ".webp")
    if not archivo.exists():
        if not clave or not it.get("foto_google"):
            return None
        r = ctx.request.get(f"https://places.googleapis.com/v1/{it['foto_google']}/media?maxWidthPx={ANCHO}",
                            headers={"X-Goog-Api-Key": clave}, timeout=30000)
        if not r.ok:
            raise ValueError(r.status)
        _guardar(r.body(), archivo)
    return archivo


def bajar_todas(ctx, items, carpeta: Path, raiz: Path):
    carpeta.mkdir(parents=True, exist_ok=True)
    usados, nuevas, fallos = set(), 0, 0
    for it in items:
        url = (it.get("imagen") or "").strip()
        if not url.startswith("http") and it.get("place_id"):
            try:
                existia = (carpeta / ("g-" + hashlib.sha1(it["place_id"].encode()).hexdigest()[:16] + ".webp")).exists()
                archivo = _foto_google(ctx, it, carpeta)
                if archivo:
                    nuevas += 0 if existia else 1
                    usados.add(archivo.name)
                    it["imagen_local"] = archivo.relative_to(raiz).as_posix()
            except Exception:
                fallos += 1
            continue
        if not url.startswith("http"):
            continue
        archivo = carpeta / _nombre(url)
        if not archivo.exists():
            try:
                origen = urlparse(it.get("url") or url)
                r = ctx.request.get(url, timeout=20000, headers={
                    "Referer": f"{origen.scheme}://{origen.netloc}/",
                    "Accept": "image/avif,image/webp,image/*,*/*;q=0.8",
                })
                if not r.ok:
                    raise ValueError(r.status)
                _guardar(r.body(), archivo)
                nuevas += 1
            except Exception:
                fallos += 1
                continue
        usados.add(archivo.name)
        it["imagen_local"] = archivo.relative_to(raiz).as_posix()
    borradas = 0
    for f in carpeta.glob("*.webp"):
        if f.name not in usados:
            f.unlink()
            borradas += 1
    print(f"Imágenes: {len(usados)} en uso, {nuevas} nuevas, {borradas} borradas, {fallos} no se pudieron bajar.")
