<?php
    header("X-Frame-Options: DENY");    //B.3 Nail
    header("Content-Security-Policy: frame-ancestors 'none';");     //B.3 Nail
    include 'app.php'; 

    if (isset($_GET['id'])) {
        $id = $_GET['id'];
        deleteStudent($id);
    }

?>