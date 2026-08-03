# AI News Analyzer


# Directory Structure

```text
...
```

### collector.py
* → collect source data
* → normalize source-specific fields
* → resolve Google RSS redirect URL if needed

### cleaner.py
* → validate fields
* → normalize text and dates
* → detect and apply duplicate policy

# Program Flow Chart

```
Google RSS
    ↓
Google redirect URL
    ↓
resolve_google_rss_link()
    ↓
Publisher URL
    ↓
Raw storage

NewsAPI
    ↓
Publisher URL
    ↓
Raw storage

cleaner.py
    ↓
Compare normalized URLs / other identifiers
    ↓
skip or upsert
    ↓
Clean storage
```

collector workflow:
```
collector.py
    |
    |-- collect_news(args)
    |       |-- get_news_via_rss()
    |       |-- get_news_via_api()
    |       |-- get_news_via_crawler()
    |               |
    |               v
    |       Normalize source-specific data
    |               |
    |               v
    |       Create common news records
    |               |
    |               v
    |       save_raw_news(articles)
    |               |
    v               v
SQLite database: raw_news table
```

# How to get the API key

## NewsAPI

1. Go to: [NewsAPI official website](https://newsapi.org)
2. Create an account.
3. After login, you will receive an API key. They're free while you are in development (not in production).
4. Set it as an environment variable:

    ```bash
    export NEWS_API_KEY="your_api_key_here" # macOS/linux bash
    $env:NEWS_API_KEY="your_api_key_here"   # windows powershell
    ```

5. Then Python can read it:
    
    ```python
    os.getenv("NEWS_API_KEY")
    ```

## Gemini API