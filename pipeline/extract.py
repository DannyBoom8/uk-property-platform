import requests
from pathlib import Path

# Files needed for our historical backfill
BACKFILL_FILES = {
    "pp_2025.csv": "https://price-paid-data.publicdata.landregistry.gov.uk/pp-2025.csv",
    "pp_2026.csv": "https://price-paid-data.publicdata.landregistry.gov.uk/pp-2026.csv",
}

# The ongoing monthly update file (used for future incremental runs)
MONTHLY_UPDATE_URL = "https://price-paid-data.publicdata.landregistry.gov.uk/pp-monthly-update-new-version.csv"

RAW_DIR = Path("data/raw")


def download_file(url: str, output_path: Path) -> None:
    """Download a file from a URL and save it to disk."""
    print(f"Downloading from {url} ...")
    response = requests.get(url, timeout=120)
    response.raise_for_status()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(response.content)
    print(f"Saved to {output_path} ({len(response.content):,} bytes)")


def download_backfill_files() -> None:
    """Download the yearly files needed for historical backfill."""
    for filename, url in BACKFILL_FILES.items():
        download_file(url, RAW_DIR / filename)


def download_monthly_update() -> None:
    """Download the current month's update file (for ongoing runs)."""
    download_file(MONTHLY_UPDATE_URL, RAW_DIR / "pp_monthly_update.csv")


if __name__ == "__main__":
    download_monthly_update()