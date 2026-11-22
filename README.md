# RedSurPlus Analyzer

Analizador pasivo de páginas y recursos observables de RedSurPlus mediante Playwright.

## Requisitos

- Windows 10/11
- Python 3.10 o superior
- Visual Studio Code
- Cuenta autorizada para acceder al sistema

## Instalación

Abre la terminal en la carpeta del proyecto y ejecuta:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m playwright install chromium
```

## Ejecución

```bash
python main.py
```

Introduce la URL, selecciona oficina e inicia sesión. La contraseña se solicita de forma oculta y no se guarda en los informes.

## Resultados

Cada ejecución crea una carpeta dentro de `resultados/` con:

- `paginas.jsonl`: estructura de páginas, campos, botones, tablas, formularios, scripts y enlaces.
- `red.jsonl`: metadatos de solicitudes y respuestas HTTP, XHR y Fetch.
- `errores.jsonl`: errores de navegación y errores JavaScript.
- `estado_rastreo.json`: rutas visitadas y pendientes.
- `rutas.csv`: inventario de rutas.
- `resumen.json`: resumen de la ejecución.

Los informes no guardan valores de campos, contraseñas, valores de cookies ni valores de localStorage/sessionStorage. Se redactan algunos parámetros sensibles de las URL.

## Alcance y seguridad

- Solo sigue enlaces del mismo origen.
- No envía formularios.
- No pulsa botones de negocio.
- No ejecuta altas, ventas, eliminaciones ni cambios.
- No descarga archivos automáticamente.
- Ctrl+C detiene el análisis.
- El rastreo termina cuando no quedan rutas internas nuevas.

La exploración no garantiza descubrir rutas no enlazadas, páginas detrás de permisos distintos, contenido que requiera interacciones manuales ni código del backend. Los endpoints se registran como metadatos; no se capturan cuerpos de respuestas para evitar almacenar datos personales o comerciales sin necesidad.

## Nota sobre HTTP

Si el sitio utiliza HTTP, las credenciales y los datos de sesión podrían transmitirse sin cifrado. Solicita HTTPS al administrador y evita redes públicas.
