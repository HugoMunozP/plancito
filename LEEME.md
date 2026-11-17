# Plancito: actualización automática de datos

GitHub Actions corre `scraper/scrape.py` todos los días a las 6:17 a. m. (hora de Lima) y actualiza dos archivos:

- `data/eventos.json` → eventos con fecha. Se actualiza todos los días.
- `data/lugares.json` → lugares sin fecha fija: tus lugares hechos a mano, tours y full days. Los tours se actualizan los lunes, o cada vez que lo corres a mano.

## Fuentes

| Fuente | Qué trae | Cómo se lee | Va a |
|---|---|---|---|
| Joinnus | Conciertos, teatro, fútbol, fiestas, etc. (incluye gratis) | Navegador invisible: la página arma las tarjetas con JavaScript | eventos |
| Teleticket | Conciertos, teatro, stand up | Navegador invisible | eventos |
| EntradaLibre | Unos 280 eventos culturales gratuitos (cine, expos, conciertos, charlas) | HTML de `entradalibre.me/event/?pg=N`, filtrado a Lima y Callao | eventos |
| Eventbrite (desactivado) | Eventos gratuitos en Lima | Muestra un captcha a los servidores de GitHub, así que está apagado en `scrape.py` | — |
| Formulario de Google | Agencias de Facebook e Instagram, municipalidades, pádel, paddle, centros culturales | CSV publicado de la hoja de respuestas | eventos |
| Civitatis | Tours, free tours y full days desde Lima | Navegador invisible | lugares |
| Inca Trilogy Tours | Full days desde Lima (Huancaya, Lachay, Antioquía, Lunahuaná…) | Su API pública de WordPress, con precios en dólares convertidos a soles | lugares |
| Google Maps (API oficial de Places) | Los restaurantes (25 por distrito), cafés (20) y bares (15) mejor calificados de Miraflores, San Isidro, San Borja y Surco, con nota de 4.5 o más | API Text Search (New). Necesita el secreto `GOOGLE_PLACES_API_KEY` | lugares |
| `data/manual/*.json` | Lo que quieras agregar a mano | Se copia tal cual | ambos |

### Fuentes que no se scrapean y por qué

- **Ministerio de Cultura (gob.pe):** gob.pe bloquea las visitas automáticas, incluso desde un navegador real ("Acceso restringido"). La mayoría de sus museos y exposiciones ya aparecen en EntradaLibre.
- **Facebook e Instagram:** bloquean el scraping y sus términos lo prohíben. Usa el formulario.
- **GetYourGuide y Viator:** tienen protección anti-bots fuerte y sus términos prohíben el scraping. Si los quieres, postula a sus programas de afiliados: te dan un feed de datos y comisión por venta.
- **Airbnb Experiences:** prohíbe el scraping. Los paseos en paddle y las escuelas de surf van a `data/manual/lugares.json`.
- **Playtomic y clubes de pádel:** son pocos clubes y cambian poco. Es más fácil cargarlos a mano en `data/manual/lugares.json`, con `"categoria": "Pádel"`.
- **Municipalidades:** sacan agendas sueltas en fechas especiales y no tienen una página fija. Usa el formulario o `data/manual/eventos.json`.
- **Eventbrite:** su API oficial ya no permite buscar eventos públicos (lo cerraron en 2020). Por eso se lee la página de resultados.

## Puesta en marcha (una sola vez)

1. (Ya hecho) Repositorio público `HugoMunozP/plancito`.
2. (Ya hecho) Los archivos de la web y del scraper ya están en el repositorio.
3. Ve a **Settings → Actions → General → Workflow permissions** y marca **Read and write permissions**.
4. Ve a **Actions → Actualizar eventos → Run workflow**. Tarda entre 5 y 10 minutos.
5. Ve a **Settings → Pages**, elige *Deploy from a branch*, la rama `main` y la carpeta `/ (root)`.

En la primera ejecución, los lugares que ya tenías en `data/lugares.json` se copian a `data/manual/lugares.json`. Desde entonces los editas ahí.

## Formulario para agencias, municipalidades y clubes

Las instrucciones están al inicio de `scraper/fuentes/formulario.py`. En resumen:

1. Crea un Google Form con estos campos: `nombre`, `fecha_inicio`, `fecha_fin`, `hora`, `lugar`, `categoria`, `precio`, `url`, `imagen`.
2. En la hoja de respuestas agrega una columna `aprobado`. Solo se publican las filas donde escribas `si`.
3. Publica la hoja como CSV y guarda el enlace en GitHub, en **Settings → Secrets and variables → Actions → Variables**, con el nombre `FORM_CSV_URL`.

## Agregar cosas a mano

Lo más fácil es usar **admin.html** (https://hugomunozp.github.io/plancito/admin.html): un formulario para agregar, editar y borrar lugares y eventos propios, con foto. Lo que guardas ahí aparece en la web en 1 o 2 minutos. Se conecta a GitHub con un token propio (Contents: Read and write, solo para este repo) que se guarda en tu navegador.

También puedes editar los archivos a mano:

`data/manual/eventos.json` es una lista con el mismo formato de los eventos:

```json
[
  {"nombre": "Tour peatonal gratuito por Barranco", "inicio": "2026-11-21", "fin": "2026-11-21",
   "hora": "10:00 am", "lugar": "Barranco", "categoria": "Paseo", "tipo": "aire", "precio": 0,
   "imagen": "", "url": "https://www.munibarranco.gob.pe", "fuente": "Municipalidad de Barranco"}
]
```

`data/manual/lugares.json` usa el formato de `lugares.json`: `nombre`, `lugar`, `categoria`, `tipo`, `precio`, `calificacion`, `atributos` y `url`.

## Protecciones

- Cada fuente corre por separado. Si una falla, se conservan sus datos anteriores y las demás siguen.
- Si en total salen menos de 15 eventos, no se sobrescribe nada y la ejecución aparece en rojo.
- Los eventos pasados se borran solos.
- No se copian las descripciones de las fuentes, solo título, fecha, lugar, precio, imagen y el link a la fuente.

## Ajustes

- Tipo de cambio para convertir dólares y euros a soles: `TIPO_CAMBIO` en `scraper/comun.py`.
- Para apagar una fuente, quítala de `FUENTES_EVENTOS` o de `FUENTES_LUGARES` en `scraper/scrape.py`.
- Si algo falla, abre **Actions**, entra a la ejecución y revisa el paso "Scrapear todas las fuentes". Al final del log hay un resumen de cuántos datos salieron de cada fuente.
