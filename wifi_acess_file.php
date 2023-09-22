<?php
//header('data: 20'); -> 헤더 설정 방법 -> 헤더의 정보를 get을 통해 아두이노로 전달한다.
// DB 연결 설정
$servername = "localhost";
$username = "..."; //ex) mysql-사용자 이름
$password = "..."; // 비밀번호
$dbname = "..."; // 스키마이름

$conn = mysqli_connect($servername, $username, $password, $dbname);


// 연결 확인
if (!$conn) {
    die("Connection failed: " . mysqli_connect_error());
}

// POST로 전송된 데이터 처리
if ($_SERVER['REQUEST_METHOD'] == 'POST') {
    $temp_data = $_POST['temp_data'];
    $humi_data = $_POST['humi_data'];
    $block_ip = $_POST['block_ip'];
    
    $sql = "CREATE TABLE IF NOT EXISTS T" ."$block_ip"." (date_time DATETIME PRIMARY KEY DEFAULT CURRENT_TIMESTAMP, temp_data FLOAT NOT NULL, humi_data FLOAT NOT NULL)";
    if ($conn->query($sql) === TRUE) {
        echo "데이터베이스에 입력되었습니다.";
    } else {
        echo "입력 중 오류 발생: " . $conn->error;
    }
    
    // 데이터베이스에 새로운 게시글 추가
    $sql = "INSERT INTO T"."$block_ip"." (temp_data, humi_data) VALUES ($temp_data, $humi_data)";

    if ($conn->query($sql) === TRUE) {
        echo "데이터베이스에 입력되었습니다.";
    } else {
        echo "입력 중 오류 발생: " . $conn->error;
    }

    // 시간별로 데이터 평균화
    $sql_insert_avg_data = "INSERT INTO T"."$block_ip"."(date_time, avg_temp, avg_humi)
    SELECT
        CONCAT(DATE_FORMAT(date_time, '%Y-%m-%d %H'), ':00:00') AS hour_date,
        AVG(temp_data) AS avg_temp,
        AVG(humi_data) AS avg_humi
    FROM T"."$block_ip"."
    GROUP BY hour_date";
    if ($conn->query($sql_insert_avg_data) === TRUE) {
        echo "평균 데이터가 추가되었습니다.";

        //db 삭제 안될시 safe 푸는 코드
        //SET SQL_SAFE_UPDATES = 0;

        // 정각 데이터는 유지하고 나머지 데이터 삭제
        $sql_delete_other_data = "DELETE FROM testdb
        WHERE DATE_FORMAT(date, '%i') <> '00'";

    if ($conn->query($sql_delete_other_data) === TRUE) {
    echo "나머지 데이터가 삭제되었습니다.";
    } else {
        echo "데이터 삭제 중 오류 발생: " . $conn->error;
    }
} else {
        echo "평균 데이터 추가 중 오류 발생: " . $conn->error;
    }
    // 데이터베이스 연결 종료
    $conn->close();
}

$usr_ip = $_GET['block_ip'];
// get을 통해 디바이스의 ip주소를 받고 이를 이용해 디바이스에 맞는 정보를 가져온다.
// DB에 저장된 가장 최근 정보를 가지고 온도 led의 on, off를 결정한다.
$sql = "SELECT temp_data FROM T"."$usr_ip"." WHERE date = (SELECT MAX(date) FROM T"."$usr_ip".")";

$result = mysqli_query($conn, $sql);

if (mysqli_num_rows($result) > 0) {
    // 결과에서 데이터를 가져옴
    $row = mysqli_fetch_assoc($result);
    $average_temp = $row['temp_data'];
    
    // 데이터를 전송
    if ($average_temp >= 30.0) {
        header('ave_temp: TEMP_LED_ON!');
    } else {
        header('ave_temp: TEMP_LED_OFF');
    }
} else {
    echo "조회된 데이터가 없습니다.";
}
// DB에 저장된 가장 최근 정보를 가지고 습도 led의 on, off를 결정한다.
$sql = "SELECT humi_data FROM T"."$usr_ip"." WHERE date = (SELECT MAX(date) FROM T"."$usr_ip".")";
$result = mysqli_query($conn, $sql);

if (mysqli_num_rows($result) > 0) {
    // 결과에서 데이터를 가져옴
    $row = mysqli_fetch_assoc($result);
    $average_humi = $row['humi_data'];
    
    // 데이터를 전송
    if ($average_humi <= 40.0) {
        header('ave_humi: HUMI_LED_ON!');
    } else {
        header('ave_humi: HUMI_LED_OFF');
    }
} else {
    echo "조회된 데이터가 없습니다.";
}
exit()
?>