<?php

require_once 'db.php';

function get_metrics_row($pdo, $location = 'ALL', $property_type = null) {
    if ($property_type === null) {
        $stmt = $pdo->prepare("
            SELECT * FROM dashboard_metrics
            WHERE location = :location AND property_type IS NULL
        ");
        $stmt->execute(['location' => $location]);
    } else {
        $stmt = $pdo->prepare("
            SELECT * FROM dashboard_metrics
            WHERE location = :location AND property_type = :property_type
        ");
        $stmt->execute(['location' => $location, 'property_type' => $property_type]);
    }

    return $stmt->fetch();
}

function get_all_property_type_rows($pdo, $location = 'ALL') {
    $stmt = $pdo->prepare("
        SELECT * FROM dashboard_metrics
        WHERE location = :location AND property_type IS NOT NULL
        ORDER BY property_type
    ");
    $stmt->execute(['location' => $location]);
    return $stmt->fetchAll();
}

function get_average_price($pdo) {
    $row = $pdo->query("
        SELECT AVG(price) AS average_price
        FROM property_sales
        WHERE ppd_category_type = 'A'
    ")->fetch();

    return round($row['average_price']);
}

function get_price_change($pdo) {
    $current_avg = $pdo->query("
        SELECT AVG(price) AS avg_price FROM property_sales
        WHERE ppd_category_type = 'A' AND date_of_transfer >= (CURRENT_DATE - INTERVAL '12 months')
    ")->fetch()['avg_price'];

    $previous_avg = $pdo->query("
        SELECT AVG(price) AS avg_price FROM property_sales
        WHERE ppd_category_type = 'A'
        AND date_of_transfer >= (CURRENT_DATE - INTERVAL '24 months')
        AND date_of_transfer < (CURRENT_DATE - INTERVAL '12 months')
    ")->fetch()['avg_price'];

    return round((($current_avg - $previous_avg) / $previous_avg) * 100, 1);
}

function get_sales_tracked($pdo) {
    $row = $pdo->query("
        SELECT COUNT(*) AS total_sales FROM property_sales
        WHERE ppd_category_type = 'A' AND date_of_transfer >= (CURRENT_DATE - INTERVAL '12 months')
    ")->fetch();

    return $row['total_sales'];
}

function get_leasehold_gap($pdo) {
    $freehold_avg = $pdo->query("
        SELECT AVG(price) AS avg_price FROM property_sales
        WHERE ppd_category_type = 'A' AND duration = 'F'
    ")->fetch()['avg_price'];

    $leasehold_avg = $pdo->query("
        SELECT AVG(price) AS avg_price FROM property_sales
        WHERE ppd_category_type = 'A' AND duration = 'L'
    ")->fetch()['avg_price'];

    return round($leasehold_avg - $freehold_avg);
}

function get_price_range($pdo) {
    return $pdo->query("
        SELECT MIN(price) AS min_price, MAX(price) AS max_price
        FROM property_sales
        WHERE ppd_category_type = 'A'
    ")->fetch();
}

function get_median_price($pdo) {
    $row = $pdo->query("
        SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price) AS median_price
        FROM property_sales WHERE ppd_category_type = 'A'
    ")->fetch();
    return round($row['median_price']);
}

function get_total_sales_value($pdo) {
    $row = $pdo->query("
        SELECT SUM(price) AS total_value FROM property_sales WHERE ppd_category_type = 'A'
    ")->fetch();
    return $row['total_value'];
}

function get_freehold_avg($pdo) {
    return round($pdo->query("
        SELECT AVG(price) AS avg_price FROM property_sales WHERE ppd_category_type = 'A' AND duration = 'F'
    ")->fetch()['avg_price']);
}

function get_leasehold_avg($pdo) {
    return round($pdo->query("
        SELECT AVG(price) AS avg_price FROM property_sales WHERE ppd_category_type = 'A' AND duration = 'L'
    ")->fetch()['avg_price']);
}

function get_freehold_share($pdo) {
    $row = $pdo->query("
        SELECT
            ROUND(100.0 * SUM(CASE WHEN duration = 'F' THEN 1 ELSE 0 END) / COUNT(*), 1) AS freehold_pct
        FROM property_sales WHERE ppd_category_type = 'A'
    ")->fetch();
    return $row['freehold_pct'];
}

function get_most_common_property_type($pdo) {
    $row = $pdo->query("
        SELECT property_type, COUNT(*) AS cnt
        FROM property_sales WHERE ppd_category_type = 'A'
        GROUP BY property_type ORDER BY cnt DESC LIMIT 1
    ")->fetch();
    return $row['property_type'];
}

function get_property_type_avg_prices($pdo) {
    $stmt = $pdo->query("
        SELECT property_type, AVG(price) AS avg_price
        FROM property_sales WHERE ppd_category_type = 'A'
        GROUP BY property_type
    ");
    return $stmt->fetchAll();
}

function get_new_build_avg($pdo) {
    return round($pdo->query("
        SELECT AVG(price) AS avg_price FROM property_sales WHERE ppd_category_type = 'A' AND old_new = 'Y'
    ")->fetch()['avg_price']);
}

function get_existing_avg($pdo) {
    return round($pdo->query("
        SELECT AVG(price) AS avg_price FROM property_sales WHERE ppd_category_type = 'A' AND old_new = 'N'
    ")->fetch()['avg_price']);
}

function get_new_build_share($pdo) {
    $row = $pdo->query("
        SELECT
            ROUND(100.0 * SUM(CASE WHEN old_new = 'Y' THEN 1 ELSE 0 END) / COUNT(*), 1) AS new_build_pct
        FROM property_sales WHERE ppd_category_type = 'A'
    ")->fetch();
    return $row['new_build_pct'];
}

function get_price_by_property_type($pdo, $location = 'ALL') {
    $stmt = $pdo->prepare("
        SELECT property_type, average_price
        FROM dashboard_metrics
        WHERE location = :location AND property_type IS NOT NULL
        ORDER BY property_type
    ");
    $stmt->execute(['location' => $location]);
    return $stmt->fetchAll();
}

function get_price_by_location($pdo, $limit = 10) {
    $stmt = $pdo->prepare("
        SELECT location, average_price
        FROM dashboard_metrics
        WHERE property_type IS NULL AND location != 'ALL'
        ORDER BY average_price DESC
        LIMIT :limit
    ");
    $stmt->bindValue('limit', $limit, PDO::PARAM_INT);
    $stmt->execute();
    return $stmt->fetchAll();
}

function get_tenure_split($pdo, $location = 'ALL') {
    $metrics = get_metrics_row($pdo, $location, null);
    return [
        'Freehold' => $metrics['freehold_share'],
        'Leasehold' => 100 - $metrics['freehold_share']
    ];
}

function get_property_type_share($pdo, $location = 'ALL') {
    $rows = get_all_property_type_rows($pdo, $location);
    $share = [];
    foreach ($rows as $row) {
        $share[$row['property_type']] = $row['type_share_pct'];
    }
    return $share;
}

function get_new_build_split($pdo, $location = 'ALL') {
    $metrics = get_metrics_row($pdo, $location, null);
    return [
        'New build' => $metrics['new_build_share'],
        'Existing' => 100 - $metrics['new_build_share']
    ];
}

function get_affordable_nearby($pdo, $limit = 10) {
    $stmt = $pdo->prepare("
        SELECT location, average_price
        FROM dashboard_metrics
        WHERE property_type IS NULL AND location != 'ALL'
        ORDER BY average_price ASC
        LIMIT :limit
    ");
    $stmt->bindValue('limit', $limit, PDO::PARAM_INT);
    $stmt->execute();
    return $stmt->fetchAll();
}

function get_most_active_areas($pdo, $limit = 10) {
    $stmt = $pdo->prepare("
        SELECT location, sales_count
        FROM dashboard_metrics
        WHERE property_type IS NULL AND location != 'ALL'
        ORDER BY sales_count DESC
        LIMIT :limit
    ");
    $stmt->bindValue('limit', $limit, PDO::PARAM_INT);
    $stmt->execute();
    return $stmt->fetchAll();
}

function get_top_types_by_volume($pdo, $location = 'ALL') {
    $stmt = $pdo->prepare("
        SELECT property_type, sales_count
        FROM dashboard_metrics
        WHERE location = :location AND property_type IS NOT NULL
        ORDER BY sales_count DESC
    ");
    $stmt->execute(['location' => $location]);
    return $stmt->fetchAll();
}

function get_recent_sales($pdo, $limit = 5) {
    $stmt = $pdo->prepare("
        SELECT postcode, property_type, price, date_of_transfer
        FROM property_sales
        WHERE ppd_category_type = 'A'
        ORDER BY date_of_transfer DESC
        LIMIT :limit
    ");
    $stmt->bindValue('limit', $limit, PDO::PARAM_INT);
    $stmt->execute();
    return $stmt->fetchAll();
}
?>