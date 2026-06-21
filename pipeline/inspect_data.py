import pandas as pd

# The Land Registry doesn't include column headers in the file,
# so we define them ourselves based on their official documentation
COLUMN_NAMES = [
    "transaction_id",
    "price",
    "date_of_transfer",
    "postcode",
    "property_type",
    "old_new",
    "duration",
    "paon",
    "saon",
    "street",
    "locality",
    "town_city",
    "district",
    "county",
    "ppd_category_type",
    "record_status",
]

df = pd.read_csv(
    "data/raw/pp_monthly_update.csv",
    header=None,          # tells pandas there's no header row in the file
    names=COLUMN_NAMES,   # so we assign our own column names instead
)

print("Shape (rows, columns):", df.shape)
print("\nFirst 5 rows:")
print(df.head())
print("\nData types:")
print(df.dtypes)
print("\nAny missing values per column:")
print(df.isnull().sum())