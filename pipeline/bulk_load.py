import os
import io
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine

from transform import load_raw_data, clean_data, validate_data, MONTHLY_COLUMNS

load_dotenv()
database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise ValueError("DATABASE_URL not found — check your .env file")

engine = create_engine(database_url)

COLUMNS = MONTHLY_COLUMNS


def bulk_copy_chunk(df_chunk: pd.DataFrame, table_name: str = "property_sales") -> None:
    """Load one chunk of rows via COPY."""
    buffer = io.StringIO()
    df_chunk[COLUMNS].to_csv(buffer, index=False, header=False)
    buffer.seek(0)

    raw_conn = engine.raw_connection()
    try:
        cursor = raw_conn.cursor()
        column_list = ", ".join(COLUMNS)
        copy_sql = f"COPY {table_name} ({column_list}) FROM STDIN WITH (FORMAT csv)"
        cursor.copy_expert(copy_sql, buffer)
        raw_conn.commit()
    finally:
        raw_conn.close()


def bulk_copy(df: pd.DataFrame, chunk_size: int = 50000, table_name: str = "property_sales") -> None:
    """Load a DataFrame via COPY, in chunks small enough to avoid pooler timeouts."""
    total = len(df)
    for start in range(0, total, chunk_size):
        chunk = df.iloc[start:start + chunk_size]
        bulk_copy_chunk(chunk, table_name)
        print(f"Copied rows {start + 1:,}–{min(start + chunk_size, total):,} of {total:,}")
    print(f"\nDone. Bulk-loaded {total:,} rows into {table_name} via COPY")


def load_yearly_file(filename: str) -> None:
    path = Path("data/raw") / filename
    raw_df = load_raw_data(path, columns=MONTHLY_COLUMNS)
    clean_df = clean_data(raw_df)
    validate_data(clean_df)
    bulk_copy(clean_df)


if __name__ == "__main__":
    load_yearly_file("pp_2025.csv")
    load_yearly_file("pp_2026.csv")