# CLI Usage Documentation

## Overview

This project provides a command-line interface (CLI) for collecting, cleaning, summarizing, analyzing, reporting, and exporting news data.

The general command format is:

```bash
python main.py <subcommand> [options]
```

Available subcommands:

| Command | Description |
|---|---|
| `fetch` | Collect news articles from external sources |
| `clean` | Validate and clean raw news data |
| `summarize` | Generate AI summaries for news articles |
| `analyze` | Perform AI-based trend and insight analysis |
| `report` | Generate analysis reports |
| `export` | Export processed news data |
| `list` | Display news articles with filtering (bonus) |
| `show` | Display details of a specific article (bonus) |
| `category` | Manage news categories (optional) |

---

# 1. 📥 `fetch`

## Purpose

Collect news articles from a configured news source such as Google News or Naver.

## Usage

```bash
python main.py fetch --source <source> [--limit <number>]
```

## Options

| Option       | Required | Default | Description                              |
| ------------ | -------- | ------- | ---------------------------------------- |
| `--source`   | Yes      | None    | News source to collect from              |
| `--limit`    | No       | `10`    | Maximum number of articles to collect    |
| `--category` | Yes      | None    | Predefined news category to collect from |
| `--query`    | Yes      | None    | Search query used to find news articles  |


## Valid Sources

Currently supported sources:

```text
google
naver
```

## Valid Examples

### (1) Fetch default number of articles

```bash
python main.py fetch --source naver --category technology --query "artificial intelligence"
```

Result:

```python
args.source = "naver"
args.limit = 10
args.category = "technology"
args.query = "artificial intelligence"
```

---

### (2) Fetch a specific number of articles

```bash
python main.py fetch --source google --limit 50 --category technology --query "artificial intelligence"
```

Result:

```python
args.source = "google"
args.limit = 50
args.category = "technology"
args.query = "artificial intelligence"
```

---

## Invalid Usage

### (1) Missing required option

Command:

```bash
python main.py fetch
```

Error:

```text
error: the following arguments are required: --source, --category, --query
```

---

### (2) Invalid source

Command:

```bash
python main.py fetch --source yahoo
```

Error:

```text
error: argument --source: invalid choice: 'yahoo'
```

Valid choices:

```text
google
naver
```

---

### (3) Missing value after option

Command:

```bash
python main.py fetch --source naver --limit
```

Error:

```text
error: argument --limit: expected one argument
```

Explanation:

`--limit` is optional, but if the option is provided, it requires a value.

---

# 2. 🧹 `clean`

## Purpose

Clean and validate raw news data.
Handles duplicate articles according to the selected policy.

## Usage

```bash
python main.py clean [--policy <policy>]
```

## Options

| Option | Required | Default | Description |
|---|---|---|---|
| `--policy` | No | `skip` | Duplicate handling strategy |

## Available Policies

| Policy | Behavior |
|---|---|
| `skip` | Ignore duplicate records |
| `upsert` | Update existing records |

---

## Valid Examples

Use default policy:

```bash
python main.py clean                # or
python main.py clean --policy skip
```

Result:

```python
args.policy = "skip"
```

---

Use upsert:

```bash
python main.py clean --policy upsert
```

Result:

```python
args.policy = "upsert"
```

---

## Invalid Usage

Invalid policy:

```bash
python main.py clean --policy delete
```

Error:

```text
error: invalid choice: 'delete'
```

Allowed values:

```text
skip
upsert
```

---

# 3. 📝 `summarize`

## Purpose

Generate AI summaries for news articles. 
The user must choose exactly one summarization target mode.

## Usage

```bash
python main.py summarize (--all | --id <id> | --unsummarized) [--limit <number>]
```

---

## Options

### Target Selection Options

These options are mutually exclusive.
Only one can be used at a time.

| Option | Description |
|---|---|
| `--all` | Summarize all news articles |
| `--id <id>` | Summarize a specific article |
| `--unsummarized` | Summarize only articles without summaries |

---

### Other Options

| Option | Required | Default | Description |
|---|---|---|---|
| `--limit` | No | `5` | Maximum number of summaries |

---

## Valid Examples

Summarize all articles:

```bash
python main.py summarize --all
```

---

Summarize one article:

```bash
python main.py summarize --id 42
```

---

Summarize only unfinished articles:

```bash
python main.py summarize --unsummarized --limit 20
```

---

## Invalid Usage

No target selected:

```bash
python main.py summarize            # or
python main.py summarize --limit 20
```

Error:

```text
error: one of the arguments --all --id --unsummarized is required
```

---

Multiple targets selected:

```bash
python main.py summarize --all --id 10
```

Error:

```text
error: argument --id: not allowed with argument --all
```

---

Missing ID value:

```bash
python main.py summarize --id
```

Error:

```text
error: argument --id: expected one argument
```

---

# 4. 📈 `analyze`

## Purpose

Perform AI-based trend analysis on collected news.

## Usage

```bash
python main.py analyze \
    --date-from YYYY-MM-DD \
    --date-to YYYY-MM-DD \
    --category CATEGORY
```

---

## Options

| Option | Required | Description |
|---|---|---|
| `--date-from` | Yes | Analysis start date |
| `--date-to` | Yes | Analysis end date |
| `--category` | Yes | News category |

---

## Valid Example

```bash
python main.py analyze \
    --date-from 2026-08-01 \
    --date-to 2026-08-10 \
    --category AI
```

---

## Invalid Usage

Missing category:

```bash
python main.py analyze --date-from 2026-08-01 --date-to 2026-08-10
```

Error:

```text
error: the following arguments are required: --category
```

---

# 5. 📊 `report`

## Purpose

Generate a report containing:

- Quality metrics
- TOP N statistics
- AI insight results
- Visualizations

## Usage

```bash
python main.py report [--format FORMAT]
```

---

## Options

| Option | Required | Default | Description |
|---|---|---|---|
| `--format` | No | `md` | Report output format |

Available formats:

```text
md
txt
```

---

## Valid Examples

Default Markdown report:

```bash
python main.py report               # or
python main.py report --format md
```

---

Text report:

```bash
python main.py report --format txt
```

---

## Invalid Usage

```bash
python main.py report --format pdf
```

Error:

```text
error: argument --format: invalid choice: 'pdf' (choose from txt, md)
```

---

# 6. 📤 `export`

## Purpose

Export news data into external files.

## Usage

```bash
python main.py export \
    --format FORMAT \
    [--status STATUS]
```

---

## Options

| Option | Required | Default | Description |
|---|---|---|---|
| `--format` | Yes | None | Export file format |
| `--status` | No | `all` | Filter by summary status |

---

## Available Formats

```text
csv
jsonl
xlsx
```

## Available Status Filters

| Status | Meaning |
|---|---|
| `all` | Export all articles |
| `summarized` | Export summarized articles only |
| `unsummarized` | Export articles without summaries |

---

## Valid Examples

```bash
python main.py export --format csv
```

---

```bash
python main.py export --format xlsx --status summarized
```

---

## Invalid Usage

Missing format:

```bash
python main.py export
```

Error:

```text
error: the following arguments are required: --format
```

---

Invalid format:

```bash
python main.py export --format pdf
```

Error:

```text
error: argument --format: invalid choice: 'pdf' (choose from csv, jsonl, xlsx)
```

---

# 7. 📋 `list` (Bonus)

## Purpose

Display news articles with optional filtering.

## Usage

```bash
python main.py list [filters]
```

---

## Options

| Option | Required | Default | Description |
|---|---|---|---|
| `--category` | No | None | Filter by category |
| `--date-from` | No | None | Start date |
| `--date-to` | No | None | End date |
| `--keyword` | No | None | Search keyword |
| `--page` | No | `1` | Page number |
| `--page-size` | No | `10` | Number of results per page |

---

## Valid Examples

Show all articles:

```bash
python main.py list
```

---

Filter by category:

```bash
python main.py list --category AI
```

---

Filter by date:

```bash
python main.py list --date-from 2026-08-01 --date-to 2026-08-10
```

---

Search keyword:

```bash
python main.py list --keyword Gemini
```

---

Pagination:

```bash
python main.py list --page 2 --page-size 20
```

---

# 8. 🔎 `show` (Bonus)

## Purpose

Display details of one article.

## Usage

```bash
python main.py show --id <article_id>
```

---

## Valid Example

```bash
python main.py show --id 15
```

---

## Invalid Usage

Missing ID:

```bash
python main.py show
```

Error:

```text
error: the following arguments are required: --id
```

---

No ID number:

```bash
python main.py show --id
```

Error:

```text
error: argument --id: expected one argument
```

---

Invalid ID format:

```bash
python main.py show --id abc
```

Error:

```text
error: argument --id: invalid int value: 'abc'
```

---

Non-existing ID:

```bash
python main.py show --id 99999
```

Behavior:

`argparse` accepts the command because `99999` is an integer.

The application must check the database and display:

```text
Error: Article with ID 99999 was not found.
```

---

# 9. 🏷️ `category`

## Purpose

Manage news categories.

## Usage

```bash
python main.py category (--list | --add NAME | --remove NAME)
```

The options are mutually exclusive.

---

## Options

| Option | Description |
|---|---|
| `--list` | Display all categories |
| `--add` | Add a new category |
| `--remove` | Remove an existing category |

---

## Valid Examples

List categories:

```bash
python main.py category --list
```

---

Add category:

```bash
python main.py category --add Business
```

---

Remove category:

```bash
python main.py category --remove Politics
```

---

## Invalid Usage

No action:

```bash
python main.py category
```

Error:

```text
error: one of the arguments --list --add --remove is required
```

---

Multiple actions:

```bash
python main.py category --list --add AI
```

Error:

```text
error: argument --add: not allowed with argument --list
```

---

# Others

## No subcommand error

No subcommand:

```bash
python main.py
```

Error:

```text
error: the following arguments are required: command
```

## Unknown subcommand error

Example:

```bash
python main.py unknown
```

Error:

```text
error: argument command: invalid choice: 'unknown' (choose from fetch, clean, summarize, analyze, report, export, list, show, category)
```

---

## Help

Display all available commands:

```bash
python main.py --help
```

Display help for a specific command:

```bash
python main.py fetch --help
```

Example:

```text
usage: main.py fetch [-h] --source {google,naver} [--limit LIMIT]

options:
  --source {google,naver}
  --limit LIMIT
```