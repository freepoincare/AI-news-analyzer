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
3. **Summarize**: Generates 3~5 sentence summaries per article using **Google Gemini**.
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
- 🔍 **News Query & Browsing**: CLI subcommands (`list`, `show`) to search and view stored articles.

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
├── output/                  # Output folder (automatic generation)
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
    ├── utils.py             # Utility functions
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
# macOS/Linux:
source .venv/bin/activate
# Windows (PowerShell):
.venv\Scripts\Activate.ps1

# 4. Install dependencies
pip install -r requirements.txt
```

<details>
<summary>[sqlite3 installation]</summary>
<br>

* sqlite3 should be also installed.

```bash
# Ubuntu / Debian / Linux Mint
sudo apt update && sudo apt install sqlite3 -y

# CentOS / RHEL / Fedora
sudo dnf install sqlite3 -y

# macOS
brew install sqlite
```
* Windows (Using Git Bash / WSL)
    * WSL (Ubuntu): Use the Ubuntu command above.
    * Git Bash: Download the `sqlite-tools-win-x64-*.zip` (or `win32-x86` depending on the system architecture) under the "precompiled binaries for Windows" section from the official [SQLite Download Page](https://www.sqlite.org/download.html), extract sqlite3.exe, and add it to your system's Environment Variables `PATH`.

<br>
</details>

---

## 🔑 API Key Setup

### 1. NewsAPI Key (Optional for `fetch --source api`)
Get a free API key at [NewsAPI.org](https://newsapi.org).

**Set environment variable:**
- **macOS/Linux:** `export NEWS_API_KEY="your_newsapi_key_here"`
- **Windows (PowerShell):** `$env:NEWS_API_KEY="your_newsapi_key_here"`


### 2. Gemini API Key (Required for `summarize` & `analyze`)
Get an API key from [Google AI Studio](https://aistudio.google.com/).

**Set environment variable:**
- **macOS/Linux:** `export GEMINI_API_KEY="your_gemini_key_here"`
- **Windows (PowerShell):** `$env:GEMINI_API_KEY="your_gemini_key_here"`

---

## 🚀 Usage

All commands are run through `main.py`.

First, check available subcommands, options, and usage instructions:
```bash
python main.py --help  # or '-h'
python main.py [ fetch | clean | summarize | analyze | report | export | list | show] -h
```

### 1. Fetch News (`fetch`)
```bash
# Fetch technology news via RSS
python main.py fetch --source rss --category technology --query semiconductor

# Fetch via NewsAPI
python main.py fetch --source api --category technology --query "artificial intelligence"

# Fetch via Web Crawler
python main.py fetch --source crawler --category technology --query AI --limit 5
```
* `limit=10` is default

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

# Summarize all clean & unsummarized articles
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
# Generate a Markdown (default) report with embedded charts
python main.py report [--category technology] [--date-from 2026-08-01] [--date-to 2026-08-07]

# Generate a plain text report
python main.py report --format txt
```
* `--category`, `--date-from`, and `--date-to` are optional.

### 6. Export Clean Data (`export`)
```bash
# Export all clean data to CSV
python main.py export --format csv --status all

# Export summarized data to Excel (.xlsx)
python main.py export --format xlsx --status summarized

# Export unsummarized data to JSONL
python main.py export --format jsonl --status unsummarized
```
* `status=all` is default

### 7. Browse Articles (`list` & `show`)
```bash
# List stored articles with optional filters
python main.py list --category technology --page 1 --page-size 10

# Show full details of an article by ID
python main.py show --id 5
```
* Filtering for `list`: use `--category`, `--date-from`, `--date-to`, `--keyword` options
* Pagination for `list`: use `--page` (default=1) & `--page-size` (default=10)

---

## 📊 Checking Output Files

After running pipeline commands, output files are organized as follows:

| Output Type | File Location | Description |
|---|---|---|
| **Database** | `data/news.db` | SQLite database storing `raw_news`, `clean_news`, and `insights`. |
| **Logs** | `logs/news_pipeline.log` | Execution logs containing timestamps and log levels. |
| **Charts** | `output/charts/chart_YYYYMMDD_HHMMSS.png` | 3~4 charts into a single 2x2 grid image. |
| **Reports** | `output/reports/report_YYYYMMDD_HHMMSS.md` | Comprehensive analysis report in Markdown format. |
| **Exports** | `output/exports/export_status_YYYYMMDD_HHMMSS.csv` | Exported dataset files (CSV, JSONL, XLSX). |

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
  python main.py summarize               python main.py analyze
  (Google Gemini 3.5 Flash)           (Multi-Article Trend Analysis)
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

<details>
<summary>[Program Flow & Error Handling]</summary>
<br>

```text
╔══════════════════════════════════════════════════════════════════════════╗
            🤖 AI News Analyzer - Program Flow & Error Handling
╚══════════════════════════════════════════════════════════════════════════╝

┌──────────────────────────────────────────────────────────────────────────┐
   🖥️  main.py  ──  CLI Entry Point

   ⚙️ config.py           Load config.json
   📋 logging_config.py   Configure log handlers
   🔧 utils.py            Date validation / format helpers

   ❌ FileNotFoundError   → config file missing  → 🛑 Immediate exit
   ❌ ValueError          → Invalid date format  → 🛑 Immediate exit
   ❌ ValueError          → Future date input    → 🛑 Immediate exit
└───────────────────────────────────┬──────────────────────────────────────┘
                                    │
                    ┌───────────────▼─────────────────┐
                           📂 Subcommand Router
                    └──┬──────┬──────┬──────┬──────┬──┘
                       │      │      │      │      │
───────────────────────▼──────▼──────▼──────▼──────▼────────────────────────

    📡 COLLECT          🧹 CLEAN         📝 SUMMARIZE       🤖 ANALYZE
    ──────────          ───────────      ────────────        ──────────
    RSS / API           Deduplication    Gemini API          Gemini API
    News fetching       Data cleaning    AI summary          Insight analysis

    ❌ ConnectionError  ❌ ValueError   ❌ APIError        ❌ APIError
    → Retry then skip    → Skip item     → Retry then skip   → Retry then skip
    ❌ Timeout          ❌ DB Error     ❌ Timeout         ❌ Timeout
    → Log warning        → 🛑 Exit       → Log warning      → Log warning
    ❌ ParseError                       ❌ QuotaExceeded   ❌ QuotaExceeded
    → Skip item                          → 🛑 Exit          → 🛑 Exit

───────────────────────────────────────────────────────────────────────────
               │              │              │               │
               └──────────────┴──────────────┴───────────────┘
                                      │
                                      ▼
                       ┌──────────────────────────┐
                          🗄️  database.py

                          SQLite
                          · raw_news
                          · clean_news
                          · insights

                          ❌ OperationalError
                          → 🛑 Immediate exit
                          ❌ IntegrityError
                          → Skip duplicate item
                          ❌ DatabaseError
                          → Log warning then retry
                       └──────────────┬───────────┘
                                      │
            ┌─────────────────────────▼──────────────────────┐
                           📂 Subcommand Router
            └──────────────────────┬─────────────────────────┘
                                   │
                      ┌────────────┴────────────┐
                      │                         │
    ──────────────────▼──────────    ───────────▼──────────────────────────

        📤 EXPORT                        📊 REPORT
        ────────────────────────         ────────────────────────
        Export to CSV / JSONL / XLSX     reporter.py
                                         · Aggregate DB statistics
        ❌ PermissionError               · Generate TXT / Markdown
        → 🛑 Immediate exit
        ❌ OSError                       ❌ ZeroDivisionError (no data)
        → 🛑 Immediate exit              → Generate empty report + warning
        ❌ No data found                 ❌ PermissionError
        → Print warning message           → 🛑 Immediate exit
                                                 │
                                         ────────▼────────────────
                                         📈 visualizer.py
                                         matplotlib 2×2 grid
                                         · Category distribution  (bar)
                                         · Daily collection trend (line)
                                         · Sentiment over time    (area/bar)
                                         · Sentiment by category  (bar) ¹

                                         ❌ Insufficient data
                                         → Skip chart, leave blank
                                         ❌ OSError (save failure)
                                         → Log warning then continue
                                         ─────────────────────────
                      │                         │
    ──────────────────▼──────────    ───────────▼──────────────────────────

    📁 output/exports/               📁 output/reports/
    ─────────────────                ─────────────────
    · export_*.csv                   · report_*.txt
    · export_*.jsonl                 · report_*.md
    · export_*.xlsx
                                     📁 output/charts/
                                     ────────────────
                                     · chart_*.png

    ───────────────────────────────────────────────────────────────────────

    📁 logs/news_pipeline.log  ◄──── Shared across all subcommands
                                     Records all errors and warnings

══════════════════════════════════════════════════════════════════════════

  Legend
  ──────
  ❌  Error / Exception point
  🛑  Immediate exit (sys.exit / raise)
  →   Processing direction
  ¹   Sentiment by category chart is hidden when --category filter is set

══════════════════════════════════════════════════════════════════════════
```

<br>
</details>


---

## ⏱️ Automated Scheduling (Cron / Task Scheduler)

How to set up periodic news collection and automated reporting using standard OS schedulers:

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