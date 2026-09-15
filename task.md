# Phase 1: Task Checklist

- `[x]` Setup Dev Environment (`.venv` and `requirements.txt`)
  - *Achievement: Created a virtual environment and installed Faker for data generation.*
- `[x]` Design & Write SQLite Schema setup script
  - *Achievement: Designed a 4-table schema (Customers, Orders, Items, Shipments) in `setup_db.py` to support messy real-world data and created the `ecommerce.db` file.*
- `[x]` Write Synthetic Data Generation script (messy/raw data)
  - *Achievement: Created and executed `generate_mock_data.py` to populate the SQLite DB with 100 fake customers and 300 orders, intentionally introducing messy formats and edge cases (lost/damaged shipments).*
- `[x]` Create Policy Documents (Markdown)
  - *Achievement: Wrote `refund_policy.md` and `shipping_policy.md` containing realistic rules and edge cases to feed into the RAG system later.*
