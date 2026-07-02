import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise ValueError("DATABASE_URL not found — check your .env file")

engine = create_engine(database_url)


def get_locations(connection):
    """Get every distinct county in the data, plus a national 'ALL' marker."""
    result = connection.execute(text("SELECT DISTINCT county FROM property_sales WHERE county IS NOT NULL"))
    locations = [row[0] for row in result]
    return ["ALL"] + locations


def calculate_trends_for(connection, location):
    """Compute one row per month for this location."""

    location_filter = "" if location == "ALL" else "AND county = :location"
    params = {"location": location}

    rows = connection.execute(text(f"""
        SELECT
            DATE_TRUNC('month', date_of_transfer)::date AS month,
            ROUND(AVG(price)) AS average_price,
            COUNT(*) AS sales_count
        FROM property_sales
        WHERE ppd_category_type = 'A' {location_filter}
        GROUP BY month
        ORDER BY month
    """), params).fetchall()

    return [
        {"location": location, "month": row.month, "average_price": row.average_price, "sales_count": row.sales_count}
        for row in rows
    ]


def run():
    with engine.begin() as connection:
        locations = get_locations(connection)
        print(f"Found {len(locations)} locations (including national)")

        connection.execute(text("TRUNCATE TABLE dashboard_trends"))

        insert_sql = text("""
            INSERT INTO dashboard_trends (location, month, average_price, sales_count)
            VALUES (:location, :month, :average_price, :sales_count)
        """)

        total_inserted = 0
        for location in locations:
            monthly_rows = calculate_trends_for(connection, location)
            for row in monthly_rows:
                connection.execute(insert_sql, row)
                total_inserted += 1
            print(f"Processed {location} ({total_inserted} rows so far)")

        print(f"\nDone. Inserted {total_inserted} rows into dashboard_trends")


if __name__ == "__main__":
    run()