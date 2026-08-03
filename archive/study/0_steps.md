# Steps to take to solve this problem

This is a well-structured data engineering and AI automation term project!

Notice the question you inserted in Section 2 (`-> ❓ 어디에 저장?`): **Summaries, raw data, cleaned data, and analysis results should all be stored in your SQLite database (or JSONL files).** SQLite is highly recommended here because relational tables make tracking statuses (like `is_summarized`) and performing queries for reports effortless.

---

# 🛠️ Step-by-Step Implementation Roadmap

## 1. Set Up Project & Database Schema:

> Step 1. First, establish your project directory structure, config file, and database schema to store raw data, clean data, summaries, and analysis reports.

### Project Directory Structure

```text
ai_news_pipeline/
├── config.json          # API keys, source URLs, deduplication settings
├── main.py              # CLI entry point (argparse)
├── database.py          # SQLite connections, tables, and CRUD operations
├── collector.py         # API, RSS, and BeautifulSoup scraper logic
├── cleaner.py           # Text normalization and deduplication
├── ai_processor.py      # LLM API calls (summaries & insights)
├── reporter.py          # Matplotlib charting & text/MD report generation
├── exporter.py          # Exporting to CSV/Excel/JSONL
└── utils.py             # Logging configuration & helper functions

```

### SQLite Database Design (`database.py`)

Create tables to store each processing stage:

* **`raw_news`**: `id`, `source`, `method` (api/rss/crawl), `raw_content`, `fetched_at`
* **`clean_news`**: `id`, `raw_id`, `title`, `content`, `category`, `published_at`, `summary`, `is_summarized`, `sentiment` (bonus)
* **`analysis_reports`**: `id`, `date_from`, `date_to`, `category`, `trends`, `keywords`, `implications`, `created_at`


## 2. Build Configuration & Logging:

> Step 2. Create `config.json` to store your LLM API keys (OpenAI / Anthropic / Gemini), news API credentials (e.g., Naver News API, NewsAPI), and deduplication policy (`skip` or `upsert`). Set up Python's `logging` module to output `INFO`, `WARNING`, and `ERROR` logs to both console and log files.


## 3. Implement Data Collection (fetch):

> Step 3. Build `collector.py` to handle both collection methods with strict HTTP timeouts (`requests.get(url, timeout=10)`) and exception handling:

* **Method 1 (API/RSS):** Fetch from a public news API (e.g., Naver News API) or RSS feeds (`feedparser`).
* **Method 2 (Crawling):** Scrape article bodies using `BeautifulSoup` or `Selenium` with polite request delays (`time.sleep(1)`).
* Save raw payloads directly into the `raw_news` database table.

```
RSS/API/crawler collection
normalization
save_raw_news()
```

## 4. Implement Data Cleaning (clean):

> Step 4. Build `cleaner.py` to process raw news into clean data:

* **Normalization:** Remove HTML tags, strip whitespace, normalize date formats (`YYYY-MM-DD`).
* **Deduplication:** Check unique identifiers (URL or hashed title/content). Apply policy:
    * `skip`: Ignore duplicate records.
    * `upsert`: Update existing record fields with new data.
* Store sanitized rows in the `clean_news` database table.

```
read raw_news
remove duplicates
clean text/date
save clean_news()
```


## 5. **Implement AI Summarization (summarize):

> Step 5. Build `ai_processor.py` for LLM integrations:

* Query `clean_news` based on CLI flags (`--unsummarized`, `--all`, or `--id <ID>`).
* Pass article body text to the AI API with a targeted prompt (e.g., *"Summarize this article in 2-3 sentences"*).
* On success, update the `summary` column and set `is_summarized = 1` in `clean_news`.
* On API failure, log the error and skip without breaking the pipeline loop.


## 6. Implement AI Insight Analysis (analyze):

> Step 6. Extend `ai_processor.py` to handle macro-level analysis:

* Fetch multiple news items filtered by date range (`--date-from`, `--date-to`) and category.
* Send concatenated titles/summaries to the AI API asking for **Trends**, **Key Keywords**, **Commonalities/Differences**, and **Implications**.
* Parse the structured response and save it into the `analysis_reports` database table.


## 7. Implement Visualization & Report Generation (report):

> Step 7. Build `reporter.py` to calculate metrics and render visualizations:

* **Matplotlib Charts:** Apply Korean font support (`plt.rc('font', family=...)`) and output PNG files for (1) Category Distribution and (2) Daily Collection Trends.
* **Report Content:** Combine quality metrics (e.g., total items collected, clean conversion rate, summary completion rate), Top-N category counts, and saved AI insights.
* Output the result to stdout and save as TXT / Markdown (`.md`) files.


## 8. Implement Data Exporter (export):

> Step 8. Build `exporter.py` using `pandas` or built-in modules (`csv`, `json`) to export records from `clean_news`:

* Accept status filters (e.g., `--status summarized`).
* Export filtered data to **CSV**, **JSONL**, or **Excel (`.xlsx`)** files.

```
read clean_news
export CSV/JSONL/XLSX
```


## 9. Assemble the CLI (main.py):

> Step 9. Connect all modules together using `argparse` sub-commands:

* `python main.py fetch --source naver --limit 20`
* `python main.py clean --policy skip`
* `python main.py summarize --unsummarized --limit 10`
* `python main.py analyze --date-from 2026-07-01 --category IT`
* `python main.py report --format md`
* `python main.py export --format excel --status summarized`

## 💡 Key Tips for Success

1. **Database Pick:** Use **SQLite** (`sqlite3`). It is native to Python, requires no separate server setup, and easily manages status transitions like `is_summarized = 0 → 1`.
2. **Korean Fonts in Matplotlib:** On Windows use `'Malgun Gothic'`, on macOS use `'AppleGothic'`, and on Linux install `nanumfont` (`'NanumGothic'`) to avoid broken font glyphs (네모 현상) on charts.
3. **Graceful Error Handling:** Wrap API and crawling requests in `try-except` blocks. If one news page fails to parse, log the warning and continue processing the rest.