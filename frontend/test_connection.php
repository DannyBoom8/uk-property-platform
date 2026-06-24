<?php

require 'config.php';

try {
    $dsn = "pgsql:host=$db_host;port=$db_port;dbname=$db_name;user=$db_user;password=$db_password";
    $pdo = new PDO($dsn);

    $result = $pdo->query("SELECT version();");
    $row = $result->fetch();

    echo "Connected successfully!<br>";
    echo "Postgres version: " . $row['version'];

} catch (PDOException $e) {
    echo "Connection failed: " . $e->getMessage();
}

?>