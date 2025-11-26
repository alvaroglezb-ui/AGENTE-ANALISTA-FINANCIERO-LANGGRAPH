# Agente Analista Financiero - RSS Scraper con Base de Datos

Sistema completo para scrapear feeds RSS financieros, almacenar artículos en base de datos y generar reportes diarios sobre MSCI World y otros índices financieros.

## 🚀 Características

- **Scraping de RSS Feeds**: Recolección automática de artículos de múltiples fuentes RSS
- **Almacenamiento en Base de Datos**: Persistencia de artículos usando SQLAlchemy (SQLite/PostgreSQL)
- **Filtrado por Fecha**: Recolección de artículos por rango de fechas o fecha específica
- **Contenido Markdown**: Descarga y conversión automática del contenido completo de cada artículo
- **Estructura Modular**: Código organizado en clases y módulos reutilizables
- **Configuración Flexible**: Soporte para SQLite (por defecto) o PostgreSQL mediante variables de entorno

## 📁 Estructura del Proyecto

```
AGENTE-ANALISTA-FINANCIERO-LANGGRAPH/
├── app/
│   ├── database/
│   │   ├── connection.py      # Gestión centralizada de conexión a BD
│   │   ├── models.py          # Modelos SQLAlchemy (Article, Collection, Extraction)
│   │   ├── db_manager.py      # Operaciones de base de datos
│   │   └── README.md          # Documentación de la base de datos
│   └── scrapers/
│       └── rss_scraper.py     # Clases RSSFetcher y Scraper
├── config/
│   └── config.json            # URLs de feeds RSS
├── examples/
│   └── database_example.py    # Ejemplo de uso de la base de datos
├── docker/
│   └── docker-compose.yml     # Configuración Docker (opcional)
├── run_scraper.py             # Script principal unificado
├── requirements.txt           # Dependencias del proyecto
└── README.md                  # Este archivo
```

## 🔧 Instalación

### Requisitos

- Python 3.8+
- pip

### Pasos

1. **Clonar el repositorio** (o descargar el código)

2. **Instalar dependencias**:
```bash
pip install -r requirements.txt
```

3. **Configurar variables de entorno** (opcional):
```bash
# Crear archivo .env en la raíz del proyecto
# Para PostgreSQL (opcional):
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=your_database

# Para OpenAI (si usas el agente):
OPENAI_API_KEY=your_openai_key
```

**Nota**: Si no configuras PostgreSQL, el sistema usará SQLite automáticamente.

## ⚙️ Configuración

### 1. Configurar Feeds RSS

Edita `config/config.json` para añadir o modificar feeds:

```json
{
  "RSS_URLS": {
    "MSCI_WORLD_NEWS_ULR": "https://ir.msci.com/rss/news-releases.xml",
    "SP500_DAILY_INSIGHTS": "https://www.spglobal.com/spdji/en/rss",
    "NASDAQ_NEWS_URL": "https://www.nasdaq.com/feed/nasdaq-original/rss.xml"
  }
}
```

### 2. Base de Datos

El sistema gestiona automáticamente la conexión:

- **SQLite (por defecto)**: No requiere configuración. Crea `rss_articles.db` automáticamente.
- **PostgreSQL**: Configura las variables de entorno en `.env` (ver sección Instalación).

## 📖 Uso

### Uso Básico - Script Unificado

El script `run_scraper.py` ejecuta todo el pipeline:

```bash
python run_scraper.py
```

Este script:
1. Crea las tablas de base de datos
2. Obtiene los feeds RSS configurados
3. Scrapea artículos de los últimos 7 días (configurable)
4. Descarga el contenido markdown de cada artículo
5. Inserta todo en la base de datos
6. Muestra un resumen

### Uso Avanzado - Programático

```python
from app.scrapers.rss_scraper import RSSFetcher, Scraper
from app.database.db_manager import DatabaseManager
from datetime import date, timedelta

# 1. Inicializar base de datos
db_manager = DatabaseManager()
db_manager.create_tables()

# 2. Obtener feeds
fetcher = RSSFetcher(config_path="config/config.json")
fetcher.fetch_all()

# 3. Scrapear artículos
scraper = Scraper(fetcher)

# Opción A: Últimos 7 días
today = date.today()
week_ago = today - timedelta(days=7)
result = scraper.collect_date_range(start_date=week_ago, end_date=today)

# Opción B: Solo hoy
result = scraper.collect_all(filter_date=today)

# Opción C: Todos los artículos
result = scraper.collect_all()

# 4. Guardar en base de datos
extraction_id = scraper.save_to_database()
print(f"Inserted extraction ID: {extraction_id}")

# 5. Consultar base de datos
collections = db_manager.get_collections()
for col in collections:
    print(f"{col['source']}: {col['article_count']} articles")
```

### Filtrado por Fecha

```python
from datetime import date, timedelta

# Filtrar por fecha específica
today = date.today()
result = scraper.collect_all(filter_date=today)

# Filtrar por rango
start = date(2025, 11, 1)
end = date(2025, 11, 30)
result = scraper.collect_date_range(start_date=start, end_date=end)

# Filtrar un feed específico
collection = scraper.collect_feed("MSCI_WORLD_NEWS_ULR", filter_date=today)
```

### Consultar Base de Datos

```python
from app.database.db_manager import DatabaseManager

db = DatabaseManager()

# Obtener todas las colecciones
collections = db.get_collections()
for col in collections:
    print(f"{col['source']}: {col['article_count']} articles")

# Obtener artículos por fuente
articles = db.get_articles_by_source("MSCI_WORLD_NEWS_ULR")
for article in articles:
    print(f"{article.title} - {article.link}")

# Obtener todos los artículos (con límite)
articles = db.get_all_articles(limit=10)
```

## 🗄️ Modelos de Base de Datos

### Article
- `id`: ID único
- `title`: Título del artículo
- `source`: Nombre de la fuente RSS
- `link`: URL del artículo (único)
- `published`: Fecha de publicación
- `content`: Contenido en markdown
- `collection_id`: Foreign key a Collection
- `created_at`: Timestamp de inserción

### Collection
- `id`: ID único
- `source`: Nombre de la fuente (único)
- `extraction_id`: Foreign key a Extraction (opcional)
- `created_at`: Timestamp de creación
- `updated_at`: Timestamp de actualización

### Extraction
- `id`: ID único
- `created_at`: Timestamp de la extracción

## 🔄 Flujo de Datos

```
RSS Feeds → RSSFetcher → Scraper → Extraction (TypedDict)
                                      ↓
                              DatabaseManager → SQLAlchemy Models
                                      ↓
                                 Database (SQLite/PostgreSQL)
```

## 📊 Ejemplos

Ver `examples/database_example.py` para un ejemplo completo de uso.

## 🔐 Variables de Entorno

### Base de Datos (PostgreSQL - Opcional)
- `POSTGRES_USER`: Usuario de PostgreSQL
- `POSTGRES_PASSWORD`: Contraseña
- `POSTGRES_HOST`: Host (default: localhost)
- `POSTGRES_PORT`: Puerto (default: 5432)
- `POSTGRES_DB`: Nombre de la base de datos

### OpenAI (Opcional - para el agente)
- `OPENAI_API_KEY`: Clave de API de OpenAI

## 🤖 Agente con LangGraph (Futuro)

El proyecto incluye estructura para un agente LangGraph que:
- Sintetiza noticias en lenguaje "for dummies"
- Genera conclusiones accionables
- Envía reportes por email

Ver `app/agent/agent.py` para más detalles (si está implementado).

## 🐳 Docker (Opcional)

Si usas PostgreSQL, puedes usar Docker:

```bash
cd docker
docker-compose up -d
```

## 📝 Notas

- **SQLite por defecto**: Si no configuras PostgreSQL, el sistema usa SQLite automáticamente
- **Detección automática**: El sistema detecta si `psycopg2` está instalado y ajusta el comportamiento
- **Sin duplicados**: Los artículos se identifican por su `link` único, evitando duplicados
- **Filtrado inteligente**: El sistema parsea fechas de múltiples formatos RSS

## 🛠️ Troubleshooting

### Error: "PostgreSQL driver not found"
- **Solución**: El sistema automáticamente usa SQLite como fallback
- **Para usar PostgreSQL**: `pip install psycopg2-binary`

### Error: "Could not determine join condition"
- **Solución**: Asegúrate de recrear las tablas ejecutando `db_manager.create_tables()`

### Feeds no se cargan
- Verifica que las URLs en `config/config.json` sean válidas
- Algunos feeds pueden requerir headers específicos (ya implementados)

## 📄 Licencia

[Especificar licencia si aplica]

## 🤝 Contribuciones

[Instrucciones de contribución si aplica]
