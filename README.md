# 📰 AI News Analyzer

An automated, CLI-driven data pipeline that collects news from multiple sources, cleans and deduplicates records in SQLite, performs AI summarization and trend insight analysis using Google Gemini, generates charts & reports, and exports data to multiple formats.

---

## 📌 Table of Contents
- [📖 Project Overview](#-project-overview)
- [✨ Key Features](#-key-features)
- [🛠️ Tech Stack](#️-tech-stack)
- [📁 Directory Structure](#-directory-structure)
- [⚙️ Installation](#️-installation)
- [🔑 API Key Setup](#-api-key-setup)
- [🚀 Usage](#-usage)
- [📊 Checking Output Files](#-checking-output-files)
- [🔄 Program Flow Chart](#-program-flow-chart)
- [⏱️ Automated Scheduling (Cron / Task Scheduler)](#️-automated-scheduling-cron--task-scheduler)

---

## 📖 Project Overview

**AI News Analyzer** demonstrates an end-to-end data pipeline in Python:
1. **Fetch**: Collects raw news articles via RSS feeds, NewsAPI, or web crawling.
2. **Clean**: Normalizes text and dates, handles missing values, and enforces deduplication policies (`skip` / `upsert`).
3. **Summarize**: Generates 3~5 sentence summaries per article using **Google Gemini 2.0 Flash**.
4. **Analyze**: Batch-analyzes filtered articles to produce structured trend insights (Key Trends, Core Keywords, Commonalities/Differences, Implications).
5. **Report**: Aggregates dataset metrics, draws `matplotlib` charts, and compiles Markdown/TXT reports.
6. **Export**: Exports dataset records to CSV, JSONL, or Excel formats.

---

## ✨ Key Features

- 🌐 **Multi-Source Fetching**: Support for RSS feeds, NewsAPI, and Web Crawling (BeautifulSoup4 / Selenium).
- 🧹 **Raw/Clean Storage Separation**: Raw data archived in `raw_news`; clean deduplicated data promoted to `clean_news`.
- 🤖 **AI-Powered Summarization & Insights**: Uses `google-genai` SDK with fallback error handling per article.
- 📈 **Automated Data Visualization**: Generates Category Distribution bar charts and Daily Collection Trend line charts.
- 📄 **Multi-Format Reporting**: Produces formatted Markdown (`.md`) and Text (`.txt`) summary reports with embedded charts.
- 💾 **Data Exporting**: Exports clean news records to CSV, JSONL, or Excel (`.xlsx`) with customizable filtering.
- 🔍 **News Query & Browsing (Bonus)**: CLI subcommands (`list`, `show`) to search and view stored articles.

---

## 🛠️ Tech Stack

- **Core**: Python 3.10+
- **AI Model**: Google Gemini API (`google-genai`)
- **Database**: SQLite3 (`data/news.db`)
- **Data Scraping & RSS**: `requests`, `beautifulsoup4`, `feedparser`, `newspaper4k`
- **Visualization & Export**: `matplotlib`, `openpyxl`
- **CLI Framework**: `argparse`

---

## 📁 Directory Structure

```text
ai-news-analyzer/
├── config.json              # Central configuration (DB path, sources, AI model, log settings)
├── main.py                  # CLI entry point dispatching subcommands
├── requirements.txt         # Project dependencies
├── README.md                # Documentation
├── data/
│   └── news.db              # SQLite database (raw_news, clean_news, insights)
├── logs/
│   └── news_pipeline.log    # Pipeline execution log file
├── output/
│   ├── charts/              # Generated matplotlib chart images (PNG)
│   ├── exports/             # Exported files (CSV, JSONL, XLSX)
│   └── reports/             # Generated reports (MD, TXT)
└── src/
    ├── __init__.py
    ├── ai_processor.py      # AI Summarization & Insight analysis logic
    ├── arg_parser.py        # argparse CLI subcommand definitions
    ├── cleaner.py           # Data normalization, cleaning, and deduplication
    ├── collector.py         # News collection (RSS, NewsAPI, Crawler)
    ├── config.py            # Configuration loader and API key validator
    ├── database.py          # SQLite connections, schema initialization, and queries
    ├── exporter.py          # Data export handlers (CSV, JSONL, Excel)
    ├── logging_config.py    # Logging setup (Stream + File handlers)
    ├── reporter.py          # Report generator linking stats, charts, and AI insights
    └── visualizer.py        # Matplotlib chart rendering logic
```

---

## ⚙️ Installation

```bash
# 1. Clone the repository
git clone <repo-url>
cd ai-news-analyzer

# 2. Create a virtual environment
python -m venv .venv

# 3. Activate the virtual environment
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt
```

---

## 🔑 API Key Setup

### 1. NewsAPI Key (Optional for `fetch --source api`)
Get a free API key at [NewsAPI.org](https://newsapi.org).

**Set environment variable:**
- **Windows (PowerShell):** `$env:NEWS_API_KEY="your_newsapi_key_here"`
- **macOS/Linux:** `export NEWS_API_KEY="your_newsapi_key_here"`

### 2. Gemini API Key (Required for `summarize` & `analyze`)
Get an API key from [Google AI Studio](https://aistudio.google.com/).

**Set environment variable:**
- **Windows (PowerShell):** `$env:GEMINI_API_KEY="your_gemini_key_here"`
- **macOS/Linux:** `export GEMINI_API_KEY="your_gemini_key_here"`

---

## 🚀 Usage

All commands are run through `main.py`.

### 1. Fetch News (`fetch`)
```bash
# Fetch technology news via RSS
python main.py fetch --source rss --category technology --query semiconductor --limit 10

# Fetch via NewsAPI
python main.py fetch --source api --category business --query economy --limit 10

# Fetch via Web Crawler
python main.py fetch --source crawler --category technology --query AI --limit 5
```

### 2. Clean & Deduplicate Data (`clean`)
```bash
# Clean raw news with default skip policy (ignores duplicates)
python main.py clean --policy skip

# Clean raw news with upsert policy (overwrites duplicates)
python main.py clean --policy upsert
```

### 3. AI Summarization (`summarize`)
> Requires `GEMINI_API_KEY`
```bash
# Summarize unsummarized articles (up to 5)
python main.py summarize --unsummarized --limit 5

# Summarize a specific article by ID
python main.py summarize --id 1

# Summarize all clean articles
python main.py summarize --all
```

### 4. AI Insight Analysis (`analyze`)
> Requires `GEMINI_API_KEY`
```bash
# Perform trend insight analysis for a category and date range
python main.py analyze --category technology --date-from 2026-01-01 --date-to 2026-12-31
```

### 5. Generate Report & Charts (`report`)
```bash
# Generate a Markdown report with embedded charts
python main.py report --format md

# Generate a plain text report
python main.py report --format txt
```

### 6. Export Clean Data (`export`)
```bash
# Export all clean data to CSV
python main.py export --format csv --status all

# Export summarized data to Excel (.xlsx)
python main.py export --format xlsx --status summarized

# Export unsummarized data to JSONL
python main.py export --format jsonl --status unsummarized
```

### 7. Browse Articles (`list` & `show`)
```bash
# List stored articles with optional filters
python main.py list --category technology --page 1 --page-size 10

# Show full details of an article by ID
python main.py show --id 1
```

---

## 📊 Checking Output Files

After running pipeline commands, output files are organized as follows:

| Output Type | File Location | Description |
|---|---|---|
| **Database** | `data/news.db` | SQLite database storing `raw_news`, `clean_news`, and `insights`. |
| **Logs** | `logs/news_pipeline.log` | Execution logs containing timestamps and log levels. |
| **Charts** | `output/charts/category_dist.png` | Bar chart of clean articles per category. |
| **Charts** | `output/charts/daily_trend.png` | Line chart of daily article collection counts. |
| **Reports** | `output/reports/report_YYYYMMDD_HHMMSS.md` | Comprehensive analysis report in Markdown format. |
| **Exports** | `output/exports/news_status_YYYYMMDD_HHMMSS.csv` | Exported dataset files (CSV, JSONL, XLSX). |

---

## 🔄 Program Flow Chart

```text
                         [ Data Sources ]
           ( RSS Feed  |  NewsAPI  |  Web Crawler )
                                |
                                v
                       python main.py fetch
                                |
                                v
                     [ SQLite: raw_news table ]
                                |
                                v
                       python main.py clean
                    ( Deduplication: skip / upsert )
                                |
                                v
                    [ SQLite: clean_news table ]
                                |
             +------------------+------------------+
             |                                     |
             v                                     v
  python main.py summarize              python main.py analyze
  (Google Gemini 2.0 Flash)             (Multi-Article Trend Analysis)
             |                                     |
             v                                     v
  Update clean_news status             [ SQLite: insights table ]
             |                                     |
             +------------------+------------------+
                                |
                                v
                       python main.py report
             (Generate matplotlib charts + MD/TXT report)
                                |
                                v
                       python main.py export
                     (Export CSV / JSONL / XLSX)
```

---

## ⏱️ Automated Scheduling (Cron / Task Scheduler)

You can set up periodic news collection and automated reporting using standard OS schedulers:

### Linux / macOS (`cron`)
Edit your crontab using `crontab -e`:

```bash
# Run news fetch and clean automatically every day at 09:00 AM
0 9 * * * cd /path/to/ai-news-analyzer && /path/to/ai-news-analyzer/.venv/bin/python main.py fetch --source rss --category technology --query AI --limit 10 >> logs/cron.log 2>&1
5 9 * * * cd /path/to/ai-news-analyzer && /path/to/ai-news-analyzer/.venv/bin/python main.py clean --policy skip >> logs/cron.log 2>&1
```

### Windows (Task Scheduler)
Create a Scheduled Task via PowerShell:
```powershell
$Action = New-ScheduledTaskAction -Execute "C:\path\to\ai-news-analyzer\.venv\Scripts\python.exe" -Argument "main.py fetch --source rss --category technology --query AI --limit 10" -WorkingDirectory "C:\path\to\ai-news-analyzer"
$Trigger = New-ScheduledTaskTrigger -Daily -At 9am
Register-ScheduledTask -TaskName "AINewsFetch" -Action $Action -Trigger $Trigger
```