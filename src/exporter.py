"""
exporter.py
    ├── export_to_csv()
    ├── export_to_jsonl()
    ├── export_to_excel()
    └── export_news()

records = get_clean_news()

if args.format == "csv":
    export_to_csv(records)

elif args.format == "jsonl":
    export_to_jsonl(records)

elif args.format == "xlsx":
    export_to_excel(records)
"""

def export_news(args):
    print(f"Exporting news data in {args.format} format with status filter: {args.status}...")
