/* =========================================================
   Plancito · medición de visitas (Google Analytics 4)
   1. Crea tu propiedad en https://analytics.google.com
   2. Copia el ID de medición (empieza con G-) y pégalo abajo, entre las comillas.
   Mientras esté vacío, no se carga nada.
   ========================================================= */
(function () {
  'use strict';
  var ID_GA4 = ''; // ← por ejemplo 'G-ABC123XYZ9'

  if (!ID_GA4 || location.hostname === 'localhost') return;
  var s = document.createElement('script');
  s.async = true;
  s.src = 'https://www.googletagmanager.com/gtag/js?id=' + ID_GA4;
  document.head.appendChild(s);
  window.dataLayer = window.dataLayer || [];
  window.gtag = function () { window.dataLayer.push(arguments); };
  window.gtag('js', new Date());
  window.gtag('config', ID_GA4);

  // Clics que importan: "Ver y comprar", "Ver ubicación" y compartir por WhatsApp
  document.addEventListener('click', function (ev) {
    var a = ev.target.closest && ev.target.closest('a[href]');
    if (!a || a.hostname === location.hostname) return;
    var texto = (a.textContent || '').trim().slice(0, 60);
    var tipo = a.hostname.indexOf('wa.me') > -1 ? 'compartir_whatsapp'
      : a.hostname.indexOf('maps.google') > -1 ? 'ver_ubicacion' : 'ver_y_comprar';
    window.gtag('event', tipo, { destino: a.hostname, texto: texto, pagina: location.pathname });
  }, true);
})();
