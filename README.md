# 🤖 AI-Powered Financial News Analyzer & Newsletter Generator

<div align="center">

**An intelligent LangGraph-based agent that automatically scrapes, analyzes, and summarizes financial news into digestible newsletters for non-expert readers.**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Latest-green.svg)](https://langchain-ai.github.io/langgraph/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-orange.svg)](https://openai.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Technology Stack](#-technology-stack)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Project Structure](#-project-structure)
- [AI Agent Capabilities](#-ai-agent-capabilities)
- [Deployment](#-deployment)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 Overview

This project is an **AI-powered financial news aggregation and analysis system** that:

- **Scrapes** financial news from multiple RSS feeds (Yahoo Finance, Google News, custom feeds)
- **Ranks** articles using AI to identify the most relevant content for young professionals
- **Translates** article titles to Spanish (or your preferred language)
- **Summarizes** complex financial news into simple, jargon-free explanations
- **Generates** beautiful HTML newsletters with structured summaries
- **Sends** daily email digests to subscribers automatically

Perfect for professionals who want to stay informed about financial markets, technology trends, and corporate news without spending hours reading technical articles.

---

## ✨ Key Features

### 🔍 Intelligent Content Curation
- **AI-Powered Ranking**: Uses LLM to score articles (0-100) based on relevance for tech-savvy professionals
- **Smart Filtering**: Prioritizes breaking news, tech companies, AI developments, and market-moving events
- **Multi-Source Aggregation**: Supports Yahoo Finance, Google News, and custom RSS feeds

### 🤖 LangGraph Agent Workflow
- **State-Based Processing**: Uses LangGraph for orchestrated article processing pipeline
- **Automatic Translation**: Translates article titles to target language using structured Pydantic outputs
- **Content Enhancement**: Fetches missing article content using web search when needed
- **Markdown Cleaning**: Removes ads, navigation, and noise to extract pure content

### 📝 Expert Summarization
- **Plain Language**: Converts complex financial jargon into simple explanations
- **Structured Format**: Generates summaries with Overview, Key Points, Why It Matters, and Simple Explanation
- **Company Context**: Automatically explains what companies do and why they're relevant
- **Jargon Explanation**: Every technical term is explained inline for complete understanding

### 📧 Newsletter Generation
- **Beautiful HTML Templates**: Professional, responsive email design
- **Multi-Language Support**: Spanish and English summaries
- **Automated Delivery**: Sends daily digests to subscriber list
- **Database Integration**: Tracks articles, prevents duplicates, and maintains history

### 🗄️ Flexible Database
- **SQLite Default**: Works out-of-the-box with no configuration
- **PostgreSQL Support**: Production-ready with environment variables
- **Automatic Schema**: Creates tables and manages relationships automatically

---

## 🏗️ Architecture

The system follows a **LangGraph-based agent architecture** with the following workflow:

```
┌─────────────────┐
│  RSS Feeds      │
│  (Yahoo, etc.)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  RSS Scraper     │
│  (Collection)    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│  LangGraph Agent Pipeline       │
│  ┌───────────────────────────┐ │
│  │  1. Rank Articles         │ │
│  │     (AI Scoring 0-100)    │ │
│  └───────────┬───────────────┘ │
│              ▼                  │
│  ┌───────────────────────────┐ │
│  │  2. Process Articles       │ │
│  │     - Translate Title     │ │
│  │     - Clean Markdown       │ │
│  │     - Fetch Content        │ │
│  │     - Generate Summary     │ │
│  └───────────┬───────────────┘ │
│              ▼                  │
│  ┌───────────────────────────┐ │
│  │  3. Store in Database      │ │
│  └───────────────────────────┘ │
└───────────┬─────────────────────┘
            │
            ▼
┌─────────────────┐
│  Database       │
│  (SQLite/PG)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Email Generator│
│  (HTML Template) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Subscribers    │
└─────────────────┘
```

### Agent State Management

The LangGraph agent uses a `TypedDict` state that tracks:
- `extraction_data`: All scraped articles organized by source
- `collection_index`: Current collection being processed
- `article_index`: Current article within collection

---

## 🛠️ Technology Stack

### Core Framework
- **LangGraph**: Agent orchestration and workflow management
- **LangChain**: LLM integration and prompt management
- **OpenAI GPT-4**: Article analysis, summarization, and translation

### Data Processing
- **SQLAlchemy**: Database ORM and connection management
- **Feedparser**: RSS feed parsing
- **BeautifulSoup4**: HTML parsing and content extraction
- **Markdownify**: HTML to Markdown conversion

### Infrastructure
- **Python 3.8+**: Core language
- **Pydantic**: Structured output validation
- **Jinja2**: HTML template rendering
- **python-dotenv**: Environment variable management

### Database
- **SQLite**: Default database (no configuration needed)
- **PostgreSQL**: Production database (via environment variables)

### Deployment
- **Render**: Cloud hosting and scheduled jobs
- **Docker**: Containerization support

---

## 📦 Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/AGENTE-ANALISTA-FINANCIERO-LANGGRAPH.git
cd AGENTE-ANALISTA-FINANCIERO-LANGGRAPH
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Set Up Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and add your configuration (see [Configuration](#-configuration) section).

---

## ⚙️ Configuration

### Required Environment Variables

```bash
# OpenAI API (Required)
OPENAI_API_KEY=your_openai_api_key_here

# Email Configuration (Required for newsletters)
EMAIL_SUBJECT=Daily News Brief
EMAIL_SENDER=your_email@gmail.com
EMAIL_PASSWORD=your_gmail_app_password  # Use App Password, not regular password
```

### Optional Environment Variables

```bash
# Language Configuration
LANGUAGE=ES  # Options: "ES" (Spanish) or "ENG" (English)

# AI Model Configuration
AGENT_MODEL=gpt-4o-mini  # Model for article processing
WEB_SEARCH_MODEL=gpt-4o  # Model for web search (when content is missing)

# Article Processing
TOP_RANK=10  # Number of top articles to include in newsletter
MAX_ARTICLES=10  # Maximum articles per RSS feed

# PostgreSQL (Optional - uses SQLite if not set)
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=rss_articles
```

### RSS Feed Configuration

Edit `config/config.json` to add or modify RSS feeds:

```json
{
  "YAHOO_RSS_URLS": {
    "FINANCE_RSS_URL": "https://news.yahoo.com/rss/finance",
    "TECH_RSS_URL": "https://news.yahoo.com/rss/tech"
  }
}
```

---

## 🚀 Usage

### Quick Start

Run the complete pipeline:

```bash
python main.py
```

This will:
1. ✅ Create database tables
2. ✅ Fetch RSS feeds
3. ✅ Scrape articles from the last day
4. ✅ Rank articles using AI
5. ✅ Process top articles (translate, summarize)
6. ✅ Store in database
7. ✅ Generate and send email newsletter

### Programmatic Usage

```python
from app.scrapers.yahoo_scraper import YahooScraper, YahooRSSFetcher
from app.database.db_manager import DatabaseManager
from app.agent.agent import ArticleSummarizerAgent
from app.agent.tools import send_daily_news_email
from datetime import date, timedelta

# 1. Initialize database
db_manager = DatabaseManager()
db_manager.create_tables()

# 2. Fetch and scrape articles
fetcher = YahooRSSFetcher(config_path="config/config.json")
fetcher.fetch_all()
scraper = YahooScraper(fetcher)

today = date.today()
extraction = scraper.collect_date_range(
    start_date=today - timedelta(days=1),
    end_date=today
)

# 3. Process with AI agent
agent = ArticleSummarizerAgent()
extraction = agent.process_extraction(extraction)

# 4. Store in database
extraction_id = db_manager.insert_extraction(extraction)

# 5. Send newsletter
recipients = db_manager.get_all_emails()
send_daily_news_email(recipients=recipients)
```

### Custom Date Ranges

```python
from datetime import date

# Last 7 days
start_date = date.today() - timedelta(days=7)
extraction = scraper.collect_date_range(start_date=start_date, end_date=date.today())

# Specific date range
extraction = scraper.collect_date_range(
    start_date=date(2025, 1, 1),
    end_date=date(2025, 1, 31)
)
```

---

## 📁 Project Structure

```
AGENTE-ANALISTA-FINANCIERO-LANGGRAPH/
├── app/
│   ├── agent/                    # AI Agent Module
│   │   ├── agent.py              # LangGraph agent implementation
│   │   ├── tools.py              # Article processing tools
│   │   ├── prompts.py            # LLM prompts for summarization
│   │   ├── schemas.py            # Pydantic models for structured output
│   │   ├── language_config.py    # Multi-language support
│   │   └── graph_schema.png       # Visual agent workflow
│   │
│   ├── database/                  # Database Module
│   │   ├── connection.py         # Database connection management
│   │   ├── models.py             # SQLAlchemy models
│   │   ├── db_manager.py        # Database operations
│   │   └── README.md            # Database documentation
│   │
│   ├── scrapers/                  # RSS Scrapers
│   │   ├── rss_scraper.py       # Generic RSS scraper
│   │   ├── yahoo_scraper.py     # Yahoo Finance scraper
│   │   └── google_news_scraper.py # Google News scraper
│   │
│   └── templates/                 # Email Templates
│       └── template.html         # HTML newsletter template
│
├── config/
│   └── config.json               # RSS feed configuration
│
├── docker/
│   └── docker-compose.yml        # Docker configuration
│
├── main.py                        # Main entry point
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment variables template
├── render.yaml                    # Render.com deployment config
└── README.md                      # This file
```

---

## 🤖 AI Agent Capabilities

### 1. Article Ranking

The agent uses an LLM to score articles (0-100) based on:
- **Technology Relevance**: AI, agents, tech companies, startups
- **Market Impact**: Stock movements, IPOs, M&A activity
- **Timeliness**: Breaking news gets higher scores
- **Audience Fit**: Content for young professionals (20-35 years)

### 2. Title Translation

- Uses **structured Pydantic output** to ensure clean translations
- Preserves company names and proper nouns
- Automatically translates to configured language (ES/ENG)

### 3. Content Processing

- **Markdown Cleaning**: Removes ads, navigation, footers
- **Web Search**: Fetches missing content using OpenAI's web search
- **Content Extraction**: Preserves important data (numbers, dates, names)

### 4. Summarization

Generates structured summaries with:
- **Overview**: One-line punchy summary
- **Key Points**: 3-5 bullet points with critical facts
- **Why It Matters**: Real-world impact explanation
- **Simple Explanation**: Complete narrative in plain language

**Special Features**:
- Explains every financial term inline
- Provides context for every company mentioned
- Uses consistent terminology throughout
- Validates coherence across all sections

### 5. Language Support

- **Spanish (ES)**: Full support with Spanish headers and content
- **English (ENG)**: Full support with English headers and content
- **Automatic Detection**: Detects language from summary headers

---

## 🚢 Deployment

### Render.com Deployment

The project includes a `render.yaml` configuration for easy deployment:

1. **Create a Render account** and connect your repository
2. **Set up a PostgreSQL database** (or use SQLite)
3. **Create a Cron Job** using the `render.yaml` configuration
4. **Add environment variables** in Render dashboard
5. **Deploy** - The job will run daily at midnight UTC

### Docker Deployment

```bash
cd docker
docker-compose up -d
```

### Manual Deployment

1. Set up a cron job or scheduled task
2. Run `python main.py` daily
3. Ensure environment variables are set
4. Monitor logs for errors

---

## 📊 Example Output

### Article Summary Format

```
RESUMEN:
Apple (fabricante de iPhone) anuncia ganancias récord de $100B

PUNTOS CLAVE:
• Apple reportó ganancias (dinero ganado) de $100 mil millones
• Las ventas de iPhone aumentaron 20% este trimestre
• La empresa anunció un nuevo programa de recompra de acciones (comprar sus propias acciones)

POR QUÉ IMPORTA:
Esto muestra que Apple sigue siendo una de las empresas más valiosas del mundo, lo que puede afectar el precio de sus acciones y la confianza de los inversores.

EXPLICACIÓN SIMPLE:
Apple ganó más dinero que nunca, principalmente porque vendió más iPhones. Cuando una empresa gana mucho dinero, su valor aumenta y los inversores quieren comprar sus acciones, lo que puede hacer que el precio suba.
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request
---

## 👤 Author

**Alvaro Gonzalez Bielza**

- LinkedIn: [@alvarogonzalezbielza](https://www.linkedin.com/in/alvarogonzalezbielza)
- GitHub: [@alvaroglezb-ui](https://github.com/alvaroglezb-ui)

---

## 🙏 Acknowledgments

- **LangGraph** team for the amazing agent framework
- **OpenAI** for GPT-4 and API access
- **LangChain** community for excellent documentation and tools

---

<div align="center">

**⭐ If you find this project useful, please consider giving it a star! ⭐**

Made with ❤️ using LangGraph and OpenAI

</div>
