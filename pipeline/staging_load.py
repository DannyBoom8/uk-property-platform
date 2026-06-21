import os
import io
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
STAGING_TABLE = "property_sales_staging"
MAIN_TABLE = "property_sales"


def create_staging_table() -> None:
    """Create the staging table if it doesn't exist, matching the main table's structure."""
    with engine.begin() as connection:
        connection.execute(text(f"""
            CREATE TABLE IF NOT EXISTS {STAGING_TABLE} (
                LIKE {MAIN_TABLE}
            );
        """))


def clear_staging_table() -> None:
    """Empty the staging table, ready for a fresh load."""
    with engine.begin() as connection:
        connection.execute(text(f"TRUNCATE TABLE {STAGING_TABLE};"))


def copy_into_staging(df: pd.DataFrame, chunk_size: int = 50000) -> None:
    """Fast COPY of the cleaned DataFrame into the (empty) staging table, in chunks."""
    total = len(df)
    for start in range(0, total, chunk_size):
        chunk = df.iloc[start:start + chunk_size]
        buffer = io.StringIO()
        chunk[COLUMNS].to_csv(buffer, index=False, header=False)
        buffer.seek(0)

        raw_conn = engine.raw_connection()
        try:
            cursor = raw_conn.cursor()
            column_list = ", ".join(COLUMNS)
            copy_sql = f"COPY {STAGING_TABLE} ({column_list}) FROM STDIN WITH (FORMAT csv)"
            cursor.copy_expert(copy_sql, buffer)
            raw_conn.commit()
        finally:
            raw_conn.close()

        print(f"Staged rows {start + 1:,}–{min(start + chunk_size, total):,} of {total:,}")


def merge_staging_into_main() -> int:
    """One set-based SQL operation: merge staging into the main table, handling conflicts."""
    update_clause = ", ".join(
        f"{col} = EXCLUDED.{col}" for col in COLUMNS if col != "transaction_id"
    )
    insert_cols = ", ".join(COLUMNS)

    merge_sql = text(f"""
        INSERT INTO {MAIN_TABLE} ({insert_cols}, updated_at)
        SELECT {insert_cols}, NOW()
        FROM {STAGING_TABLE}
        ON CONFLICT (transaction_id)
        DO UPDATE SET {update_clause}, updated_at = NOW();
    """)

    with engine.begin() as connection:
        result = connection.execute(merge_sql)
        return result.rowcount


def load_via_staging(filename: str) -> None:
    """Full pipeline: extract-clean-validate, COPY into staging, merge into main, clear staging."""
    path = Path("data/raw") / filename
    raw_df = load_raw_data(path, columns=MONTHLY_COLUMNS)
    clean_df = clean_data(raw_df)
    validate_data(clean_df)

    create_staging_table()
    clear_staging_table()
    copy_into_staging(clean_df)

    print("Merging staging into main table...")
    affected = merge_staging_into_main()
    print(f"Merge complete — {affected:,} rows affected in {MAIN_TABLE}")

    clear_staging_table()
    print("Staging table cleared, ready for next run.")


if __name__ == "__main__":
    load_via_staging("pp_monthly_update.csv")