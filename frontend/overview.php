<!DOCTYPE html>
<html>
<head>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
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
    $price_by_location = get_price_by_location($pdo);
    $tenure_split = get_tenure_split($pdo);
    $type_share = get_property_type_share($pdo);
    $new_build_split = get_new_build_split($pdo);
    $metrics = get_metrics_row($pdo, 'ALL', null);
    $chart_a_data = get_price_by_property_type($pdo);

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

<div style="display: flex; gap: 20px; margin-top: 2rem;">

    <div style="max-width: 500px; flex: 1;">
        <div style="display: flex; gap: 8px; margin-bottom: 10px;">
            <select id="chartA-data">
                <option value="type">Price by property type</option>
                <option value="location">Price by location</option>
            </select>
            <select id="chartA-type">
                <option value="bar">Bar</option>
                <option value="line">Line</option>
            </select>
        </div>
        <canvas id="chartA"></canvas>
    </div>

    <div style="max-width: 500px; flex: 1;">
        <div style="display: flex; gap: 8px; margin-bottom: 10px;">
            <select id="chartB-data">
                <option value="tenure">Freehold vs leasehold</option>
                <option value="typeShare">Property type share</option>
                <option value="newBuild">New build vs existing</option>
            </select>
            <select id="chartB-type">
                <option value="pie">Pie</option>
                <option value="doughnut">Doughnut</option>
            </select>
        </div>
        <canvas id="chartB"></canvas>
    </div>

</div>

<script>
// All the data PHP fetched, handed to JavaScript once
const chartDatasets = {
    type: {
        labels: <?= json_encode(array_column($chart_a_data, 'property_type')) ?>,
        values: <?= json_encode(array_column($chart_a_data, 'average_price')) ?>
    },
    location: {
        labels: <?= json_encode(array_column($price_by_location, 'location')) ?>,
        values: <?= json_encode(array_column($price_by_location, 'average_price')) ?>
    },
    tenure: {
        labels: <?= json_encode(array_keys($tenure_split)) ?>,
        values: <?= json_encode(array_values($tenure_split)) ?>
    },
    typeShare: {
        labels: <?= json_encode(array_keys($type_share)) ?>,
        values: <?= json_encode(array_values($type_share)) ?>
    },
    newBuild: {
        labels: <?= json_encode(array_keys($new_build_split)) ?>,
        values: <?= json_encode(array_values($new_build_split)) ?>
    }
};

let chartA, chartB;

function renderChartA() {
    const dataKey = document.getElementById('chartA-data').value;
    const chartType = document.getElementById('chartA-type').value;
    const dataset = chartDatasets[dataKey];

    if (chartA) chartA.destroy();
    chartA = new Chart(document.getElementById('chartA'), {
        type: chartType,
        data: {
            labels: dataset.labels,
            datasets: [{ label: 'Average price', data: dataset.values, backgroundColor: '#378ADD', borderColor: '#378ADD' }]
        },
        options: { responsive: true, plugins: { legend: { display: false } } }
    });
}

function renderChartB() {
    const dataKey = document.getElementById('chartB-data').value;
    const chartType = document.getElementById('chartB-type').value;
    const dataset = chartDatasets[dataKey];

    if (chartB) chartB.destroy();
    chartB = new Chart(document.getElementById('chartB'), {
        type: chartType,
        data: {
            labels: dataset.labels,
            datasets: [{ data: dataset.values, backgroundColor: ['#378ADD', '#D4537E', '#1D9E75', '#BA7517', '#6B5DD3'] }]
        },
        options: { responsive: true }
    });
}

document.getElementById('chartA-data').addEventListener('change', renderChartA);
document.getElementById('chartA-type').addEventListener('change', renderChartA);
document.getElementById('chartB-data').addEventListener('change', renderChartB);
document.getElementById('chartB-type').addEventListener('change', renderChartB);

renderChartA();
renderChartB();
</script>

<?php
} catch (PDOException $e) {
    echo "<script>document.getElementById('loading-overlay').style.display = 'none';</script>";
    echo "Error: " . $e->getMessage();
}
?>

</body>
</html>