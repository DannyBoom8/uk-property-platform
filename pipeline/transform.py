import pandas as pd
from pathlib import Path

# Monthly update files include record_status; yearly files do not
MONTHLY_COLUMNS = [
    "transaction_id", "price", "date_of_transfer", "postcode", "property_type",
    "old_new", "duration", "paon", "saon", "street", "locality",
    "town_city", "district", "county", "ppd_category_type", "record_status",
]

YEARLY_COLUMNS = [
    "transaction_id", "price", "date_of_transfer", "postcode", "property_type",
    "old_new", "duration", "paon", "saon", "street", "locality",
    "town_city", "district", "county", "ppd_category_type",
]

RAW_PATH = Path("data/raw/pp_monthly_update.csv")  # kept for backward compatibility with existing calls


def load_raw_data(path: Path, columns: list[str] = MONTHLY_COLUMNS) -> pd.DataFrame:
    """Load a raw Land Registry CSV with the appropriate column names."""
    df = pd.read_csv(
        path,
        header=None,
        names=columns,
        dtype={"transaction_id": str},  # force this column to be read as text, never inferred as numeric
    )
    print(f"Loaded {len(df):,} raw rows from {path.name}")
    return df

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Apply cleaning and type conversions based on what we learned inspecting the data."""

    # Strip the curly braces from transaction_id, e.g. {50D10B83-...} -> 50D10B83-...
    df["transaction_id"] = df["transaction_id"].str.strip("{}")

    # Convert date_of_transfer from text to a real date type
    df["date_of_transfer"] = pd.to_datetime(df["date_of_transfer"]).dt.date

    # Trim whitespace on all text columns
    text_columns = [
        "postcode", "property_type", "old_new", "duration", "paon", "saon",
        "street", "locality", "town_city", "district", "county", "ppd_category_type",
    ]
    if "record_status" in df.columns:
        text_columns.append("record_status")

    for col in text_columns:
        df[col] = df[col].str.strip()

    return df


def validate_data(df: pd.DataFrame) -> None:
    """A few basic sanity checks — fail loudly if something looks structurally wrong."""

    assert df["transaction_id"].is_unique, "Found duplicate transaction_id values!"
    assert df["price"].min() > 0, "Found a non-positive price!"
    assert df["town_city"].isnull().sum() == 0, "Found unexpected nulls in town_city!"
    assert df["date_of_transfer"].isnull().sum() == 0, "Found unexpected nulls in date_of_transfer!"

    print("All validation checks passed.")


if __name__ == "__main__":
    raw_df = load_raw_data(RAW_PATH)
    clean_df = clean_data(raw_df)
    validate_data(clean_df)

    print("\nCleaned data sample:")
    print(clean_df.head())
    print("\nData types after cleaning:")
    print(clean_df.dtypes)