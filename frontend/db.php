<?php

require_once 'config.php';

function get_db_connection() {
    global $db_host, $db_port, $db_name, $db_user, $db_password;

    $dsn = "pgsql:host=$db_host;port=$db_port;dbname=$db_name;user=$db_user;password=$db_password";
    return new PDO($dsn);
}

?>