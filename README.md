## Agente diario MSCI World

El repositorio contiene un agente construido con LangGraph que:
- Consulta varias fuentes RSS relacionadas con MSCI World y macroeconomía.
- Sintetiza las noticias en lenguaje “for dummies” y resalta conclusiones accionables.
- Compone y envía un correo diario con el resumen.

### Estructura principal

- `rss_scraper.py`: clase `RSSScraper` encargada de leer los feeds y normalizar los artículos.
- `agent.py`: clase `MSCIWorldAgent` que orquesta LangGraph, resume con el LLM y construye el correo.

### Fuentes configuradas
Las URLs se encuentran en `config.json`.

- `MSCI_WORLD_NEWS_ULR`: https://ir.msci.com/rss/news-releases.xml
- `IDEAS_INVERSION_BOLSA`: https://es.investing.com/rss/news_1065.rss
- `NOTICIAS_ECONOMICAS`: https://es.investing.com/rss/news_14.rss

Puedes añadir o quitar feeds editando ese archivo.

### Requisitos

```
pip install -r requirements.txt
```

Asegúrate de tener configurada tu clave de OpenAI (`OPENAI_API_KEY`).

### Variables de entorno para el correo

| Variable | Descripción |
| --- | --- |
| `REPORT_SENDER` | Dirección del remitente |
| `REPORT_RECIPIENTS` | Lista de destinatarios separada por comas |
| `SMTP_HOST` | Host SMTP (ej. `smtp.gmail.com`) |
| `SMTP_PORT` | Puerto SMTP (587 por defecto) |
| `SMTP_USERNAME` | Usuario SMTP |
| `SMTP_PASSWORD` | Contraseña o token SMTP |
| `DRY_RUN` | Ponla en `true` para no enviar emails durante las pruebas |

### Uso

```
python agent.py --limit 3 --language es --subject-prefix "Reporte MSCI World"
```

Parámetros disponibles:
- `--limit`: número de artículos a leer por feed (default 3).
- `--language`: idioma del resumen (default `es`).
- `--temperature`: creatividad del modelo (default 0.2).
- `--dry-run`: imprime el correo sin enviarlo.

### Automatización diaria

Ejemplo de tarea cron (macOS/Linux) para ejecutar a las 7:00:

```
0 7 * * * cd /ruta/al/proyecto && /usr/bin/env OPENAI_API_KEY=... REPORT_SENDER=... python agent.py --limit 5 >> agent.log 2>&1
```

Asegúrate de exportar las variables de entorno en el mismo comando o en tu shell de inicio.

