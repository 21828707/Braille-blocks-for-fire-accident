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

    // 데이터베이스에 새로운 게시글 추가
    $sql = "INSERT INTO temp (temp_data, humi_data, ip) VALUES ($temp_data, $humi_data, '$block_ip')";

    if ($conn->query($sql) === TRUE) {
        echo "데이터베이스에 입력되었습니다.";
    } else {
        echo "입력 중 오류 발생: " . $conn->error;
    }

    // 데이터베이스 연결 종료
    $conn->close();
}

$usr_ip = $_GET['block_ip'];
// get을 통해 디바이스의 ip주소를 받고 이를 이용해 디바이스에 맞는 정보를 가져온다.
// DB에 저장된 가장 최근 정보를 가지고 온도 led의 on, off를 결정한다.
$sql = "SELECT temp_data FROM temp WHERE ip = '$usr_ip' AND date = (SELECT MAX(date) FROM temp)";

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
$sql = "SELECT humi_data FROM temp WHERE ip = '$usr_ip' AND date = (SELECT MAX(date) FROM temp)";
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