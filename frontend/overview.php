<!DOCTYPE html>
<html>
<head>
    <style>
        #loading-overlay {
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background: white;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            z-index: 9999;
            font-family: Arial, sans-serif;
        }
        .spinner {
            width: 40px;
            height: 40px;
            border: 4px solid #e0e0e0;
            border-top: 4px solid #378ADD;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-bottom: 1rem;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        #fact-text {
            max-width: 380px;
            text-align: center;
            color: #555;
            font-size: 14px;
            min-height: 40px;
            margin-top: 1rem;
        }
    </style>
</head>
<body>

<div id="loading-overlay">
    <div class="spinner"></div>
    <p style="font-weight: 500;">Loading property data, please wait...</p>
    <p id="fact-text"></p>
</div>

<script>
const facts = [
    "The first recorded house sale in England dates back centuries before modern Land Registry records began.",
    "Red brick became popular in UK housing in the Victorian era due to mass production of bricks.",
    "Buckingham Palace is estimated to be worth well over £1 billion, though it has never been sold.",
    "Terraced houses became common in the UK during rapid urban growth in the 18th and 19th centuries.",
    "The UK's leasehold system dates back to medieval land law.",
    "Detached houses are generally the most expensive property type across most of the UK.",
    "Flats and maisonettes make up a large share of property sales in major UK cities.",
    "The HM Land Registry has recorded property sales data since 1995.",
    "Stamp duty has existed in England in some form since 1694.",
    "The average UK home today is significantly smaller than homes built in the early 20th century.",
    "Greater London consistently has some of the highest average property prices in the UK.",
    "Freehold ownership means owning the property and the land it sits on outright.",
    "New build homes often carry a price premium compared to similar existing properties.",
    "The UK property market is famously seasonal, with spring and autumn often seeing more transactions.",
    "Victorian terraces remain some of the most sought-after property styles in UK cities today.",
    "The Georgian era introduced many of the symmetrical townhouse designs still admired today.",
    "Scotland and Northern Ireland have separate property registries from HM Land Registry.",
    "Semi-detached houses became especially popular in the UK during the interwar housing boom.",
    "Property prices in the UK are recorded at the point of registration, which can lag the actual sale by weeks.",
    "The world's narrowest house in the UK is just over 5 feet wide."
];

let factIndex = 0;
const factText = document.getElementById('fact-text');
factText.textContent = facts[0];

setInterval(() => {
    factIndex = (factIndex + 1) % facts.length;
    factText.textContent = facts[factIndex];
}, 5000);
</script>

<?php
ob_flush();
flush();

require_once 'queries.php';

try {
    $pdo = get_db_connection();
    $query_start = microtime(true);

    $metrics = get_metrics_row($pdo, 'ALL', null);

    $average_price = $metrics['average_price'];
    $percent_change = $metrics['price_change_pct'];
    $sales_tracked = $metrics['sales_count_12m'];
    $leasehold_gap = $metrics['leasehold_avg'] - $metrics['freehold_avg'];
    $price_min = $metrics['price_min'];
    $price_max = $metrics['price_max'];

    $query_time = round(microtime(true) - $query_start, 4);
?>

<script>
document.getElementById('loading-overlay').style.display = 'none';
</script>

<div style="font-family: Arial, sans-serif; padding: 2rem;">
    <h2>UK Property Overview</h2>
    <p>Average price: £<?= number_format($average_price) ?></p>
    <p>Price change vs. previous 12 months: <?= $percent_change ?>%</p>
    <p>Sales tracked (last 12 months): <?= number_format($sales_tracked) ?></p>
    <p>Leasehold vs freehold gap: £<?= number_format($leasehold_gap) ?></p>
    <p>Price range: £<?= number_format($price_min) ?> – £<?= number_format($price_max) ?></p>
    <p style="color: #888; font-size: 13px;">Data computed in <?= $query_time ?> seconds</p>
</div>

<?php
} catch (PDOException $e) {
    echo "<script>document.getElementById('loading-overlay').style.display = 'none';</script>";
    echo "Error: " . $e->getMessage();
}
?>

</body>
</html>