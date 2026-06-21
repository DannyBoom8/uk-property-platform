import os
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from transform import load_raw_data, clean_data, validate_data, MONTHLY_COLUMNS

load_dotenv()
database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise ValueError("DATABASE_URL not found — check your .env file")

engine = create_engine(database_url)

COLUMNS = MONTHLY_COLUMNS


def upsert_rows(df: pd.DataFrame, chunk_size: int = 2000) -> None:
    """Insert new rows, or update existing ones (matched by transaction_id), in batches."""

    insert_cols = ", ".join(COLUMNS)
    value_placeholders = ", ".join(f":{col}" for col in COLUMNS)
    update_clause = ", ".join(
        f"{col} = EXCLUDED.{col}" for col in COLUMNS if col != "transaction_id"
    )

    upsert_sql = text(f"""
        INSERT INTO property_sales ({insert_cols}, updated_at)
        VALUES ({value_placeholders}, NOW())
        ON CONFLICT (transaction_id)
        DO UPDATE SET {update_clause}, updated_at = NOW()
    """)

    records = df[COLUMNS].to_dict(orient="records")
    total = len(records)

    for start in range(0, total, chunk_size):
        chunk = records[start:start + chunk_size]
        with engine.begin() as connection:
            connection.execute(upsert_sql, chunk)
        print(f"Upserted rows {start + 1:,}–{start + len(chunk):,} of {total:,}")

    print(f"\nDone. Upserted {total:,} rows total into property_sales")


def load_file(filename: str) -> None:
    """Run the full extract-clean-validate-upsert pipeline for a given raw file."""
    path = Path("data/raw") / filename
    raw_df = load_raw_data(path, columns=MONTHLY_COLUMNS)
    clean_df = clean_data(raw_df)
    validate_data(clean_df)
    upsert_rows(clean_df)


if __name__ == "__main__":
    load_file("pp_monthly_update.csv")