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


def calculate_metrics_for(connection, location, property_type):
    
    """Compute every dashboard_metrics column for one location + property_type combination."""

    location_filter = "" if location == "ALL" else "AND county = :location"
    type_filter = "AND property_type = :property_type" if property_type else "AND property_type IS NOT NULL"

    params = {"location": location, "property_type": property_type}

    base_where = f"WHERE ppd_category_type = 'A' {location_filter}"

    # Average, median, min, max, count, total value — scoped to this location, and to this property_type if set
    type_clause = "AND property_type = :property_type" if property_type else ""
    row = connection.execute(text(f"""
        SELECT
            ROUND(AVG(price)) AS average_price,
            ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price)) AS median_price,
            MIN(price) AS price_min,
            MAX(price) AS price_max,
            COUNT(*) AS sales_count,
            SUM(price) AS total_sales_value
        FROM property_sales
        {base_where} {type_clause}
    """), params).fetchone()

    if row.sales_count == 0:
        return None  # no data for this combination — skip it

    # Price change vs previous 12-month period
    change_row = connection.execute(text(f"""
        SELECT
            (SELECT AVG(price) FROM property_sales {base_where} {type_clause}
                AND date_of_transfer >= (CURRENT_DATE - INTERVAL '12 months')) AS current_avg,
            (SELECT AVG(price) FROM property_sales {base_where} {type_clause}
                AND date_of_transfer >= (CURRENT_DATE - INTERVAL '24 months')
                AND date_of_transfer < (CURRENT_DATE - INTERVAL '12 months')) AS previous_avg
    """), params).fetchone()

    price_change_pct = None
    if change_row.current_avg and change_row.previous_avg:
        price_change_pct = round(((change_row.current_avg - change_row.previous_avg) / change_row.previous_avg) * 100, 1)
        # Sales count, last 12 months specifically
    
    count_12m_row = connection.execute(text(f"""
        SELECT COUNT(*) AS count_12m
        FROM property_sales
        {base_where} {type_clause}
        AND date_of_transfer >= (CURRENT_DATE - INTERVAL '12 months')
    """), params).fetchone()
    sales_count_12m = count_12m_row.count_12m

    # Freehold / leasehold
    tenure_row = connection.execute(text(f"""
        SELECT
            ROUND(AVG(CASE WHEN duration = 'F' THEN price END)) AS freehold_avg,
            ROUND(AVG(CASE WHEN duration = 'L' THEN price END)) AS leasehold_avg,
            ROUND(100.0 * SUM(CASE WHEN duration = 'F' THEN 1 ELSE 0 END) / COUNT(*), 1) AS freehold_share
        FROM property_sales {base_where} {type_clause}
    """), params).fetchone()

    # Most common property type (only meaningful for the "all types" row)
    most_common_type = None
    if property_type is None:
        common_row = connection.execute(text(f"""
            SELECT property_type FROM property_sales {base_where}
            GROUP BY property_type ORDER BY COUNT(*) DESC LIMIT 1
        """), params).fetchone()
        most_common_type = common_row.property_type if common_row else None

    # Property type share (only meaningful when a specific type is set)
    type_share_pct = None
    if property_type:
        share_row = connection.execute(text(f"""
            SELECT
                ROUND(100.0 * SUM(CASE WHEN property_type = :property_type THEN 1 ELSE 0 END) / COUNT(*), 1) AS share
            FROM property_sales {base_where}
        """), params).fetchone()
        type_share_pct = share_row.share

    # New build / existing
    build_row = connection.execute(text(f"""
        SELECT
            ROUND(AVG(CASE WHEN old_new = 'Y' THEN price END)) AS new_build_avg,
            ROUND(AVG(CASE WHEN old_new = 'N' THEN price END)) AS existing_avg,
            ROUND(100.0 * SUM(CASE WHEN old_new = 'Y' THEN 1 ELSE 0 END) / COUNT(*), 1) AS new_build_share
        FROM property_sales {base_where} {type_clause}
    """), params).fetchone()

    return {
        "location": location,
        "property_type": property_type,
        "average_price": row.average_price,
        "median_price": row.median_price,
        "price_min": row.price_min,
        "price_max": row.price_max,
        "price_change_pct": price_change_pct,
        "sales_count": row.sales_count,
        "sales_count_12m": sales_count_12m,
        "total_sales_value": row.total_sales_value,
        "freehold_avg": tenure_row.freehold_avg,
        "leasehold_avg": tenure_row.leasehold_avg,
        "freehold_share": tenure_row.freehold_share,
        "type_share_pct": type_share_pct,
        "most_common_type": most_common_type,
        "new_build_avg": build_row.new_build_avg,
        "existing_avg": build_row.existing_avg,
        "new_build_share": build_row.new_build_share,
    }


def run():
    property_types = [None, "D", "S", "T", "F", "O"]

    with engine.begin() as connection:
        locations = get_locations(connection)
        print(f"Found {len(locations)} locations (including national)")

        connection.execute(text("TRUNCATE TABLE dashboard_metrics"))

        insert_sql = text("""
            INSERT INTO dashboard_metrics (
                location, property_type, average_price, median_price, price_min, price_max,
                price_change_pct, sales_count, sales_count_12m, total_sales_value, freehold_avg, leasehold_avg,
                freehold_share, type_share_pct, most_common_type, new_build_avg, existing_avg, new_build_share
            ) VALUES (
                :location, :property_type, :average_price, :median_price, :price_min, :price_max,
                :price_change_pct, :sales_count, :sales_count_12m, :total_sales_value, :freehold_avg, :leasehold_avg,
                :freehold_share, :type_share_pct, :most_common_type, :new_build_avg, :existing_avg, :new_build_share
            )
        """)

        total_inserted = 0
        for location in locations:
            for property_type in property_types:
                metrics = calculate_metrics_for(connection, location, property_type)
                if metrics:
                    connection.execute(insert_sql, metrics)
                    total_inserted += 1

            print(f"Processed {location} ({total_inserted} rows so far)")

        print(f"\nDone. Inserted {total_inserted} rows into dashboard_metrics")


if __name__ == "__main__":
    run()