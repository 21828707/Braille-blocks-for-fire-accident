#pip install flask
#pip install request
#pip install cryptography
from flask import Flask, request, jsonify, escape

app = Flask(__name__)


# MySQL 데이터베이스 연결 설정
#pip install pymysql
#pip install schedule
import pymysql.cursors
import schedule
import time


conn = pymysql.connect(host='localhost',
                            user='root',  # MySQL 사용자 이름
                            password='******', # MySQL 비밀번호
                            db='******', # MySQL 스키마 이름
                            charset='utf8mb4',
                            cursorclass=pymysql.cursors.DictCursor)
fire = 30.0
plz = "00"

def automatic_delete():
    global plz
    delete_data_sql = f"""
    DELETE FROM T{plz}
    WHERE date_time < DATE_SUB(NOW(), INTERVAL 1 HOUR)"""
    conn.cursor().execute(delete_data_sql)
    conn.commit()

def automatic_counting():
    global plz
    insert_avg_data_sql = f"""
    INSERT IGNORE INTO T1{plz} (hour_date_time, avg_temp_data, avg_humi_data)
    SELECT
        DATE_FORMAT(date_time, '%Y-%m-%d %H:00:00'),
        AVG(temp_data) AS avg_temp_data,
        AVG(humi_data) AS avg_humi_data
    FROM T{plz}
    GROUP BY DATE_FORMAT(date_time, '%Y-%m-%d %H:00:00')
    ON DUPLICATE KEY UPDATE
    avg_temp_data = (SELECT AVG(temp_data) AS avg_temp_data FROM T{plz} GROUP BY DATE_FORMAT(date_time, '%Y-%m-%d %H:00:00')),
    avg_humi_data = (SELECT AVG(humi_data) AS avg_humi_data FROM T{plz} GROUP BY DATE_FORMAT(date_time, '%Y-%m-%d %H:00:00'))"""
    conn.cursor().execute(insert_avg_data_sql)
    conn.commit()

schedule.every().hour.at(":00").do(automatic_counting) #1시간마다 1번씩 시간 단위 취합.
schedule.every().hour.at(":00").do(automatic_delete)
#위는 각각 시간 당 취합 및 삭제를 위한 함수 및 schedule등록.


@app.route('/')
def hello():
    name = request.args.get("name", "World")
    return f'Hello, {escape(name)}!'

@app.route('/process_data', methods=['POST'])
def process_data():
    if request.method == 'POST':
        temp_data = request.form['temp_data']
        humi_data = request.form['humi_data']
        block_Num = request.form['block_Num']
        
        ji = int(block_Num)
        number = 2*(ji-1) if ji != 1 else 1 # 2진수와 유사한 방식을 차용 각 디바이스의 고유번호를 이용해 화재 위치를 숫자의 합으로 표현한다. ex) 1=>2^0=1, 2=>2^1=2, 3=>2^2=4
        global plz # 시간 당 집계 및 삭제 함수에서 테이블의 이름을 지정해주는 값을 post방식으로 받아오기에 전역 변수 처리하여 제공.
        plz = str(block_Num)
        
        try:
            with conn.cursor() as cursor:
                # 테이블 생성
                create_table_sql = f"CREATE TABLE IF NOT EXISTS T{block_Num} (date_time DATETIME PRIMARY KEY DEFAULT CURRENT_TIMESTAMP, temp_data FLOAT NOT NULL, humi_data FLOAT NOT NULL)"
                cursor.execute(create_table_sql)
                #평균집계 테이블 생성
                create_table_avg_sql = f"CREATE TABLE IF NOT EXISTS T1{block_Num} (hour_date_time DATETIME PRIMARY KEY , avg_temp_data FLOAT NOT NULL, avg_humi_data FLOAT NOT NULL)"
                cursor.execute(create_table_avg_sql)

                schedule.run_pending() #이전 값 취합과 삭제가 완료된 후 

                temp_aware_sql = f"SELECT avg_temp_data FROM T1{block_Num} WHERE hour_date_time = (SELECT MAX(hour_date_time) FROM T1{block_Num})"
                cursor.execute(temp_aware_sql)
                tmp_result = cursor.fetchone()
                global fire
                if tmp_result is not None:
                    latest_temp = tmp_result['avg_temp_data']
                    sub = fire - latest_temp
                    if sub < 5.0:
                        fire = fire + 5.0
                    elif sub >10.0:
                        fire = fire - 5.0
                
                # 데이터 삽입
                insert_data_sql = f"INSERT INTO T{block_Num} (temp_data, humi_data) VALUES ({temp_data}, {humi_data})"
                cursor.execute(insert_data_sql)

                fire_awareness_sql = f"INSERT INTO fireNow(name, switch, num) VALUES('T{block_Num}', false, {number}) ON DUPLICATE KEY UPDATE switch=false"
                if float(temp_data) >= fire:
                    fire_awareness_sql = f"INSERT INTO fireNow(name, switch, num) VALUES('T{block_Num}', true, {number}) ON DUPLICATE KEY UPDATE switch=true"
                cursor.execute(fire_awareness_sql)
                
        finally:
            conn.commit()
            return None

#get을 통해 디바이스의 ip주소를 받고 이를 이용해 디바이스에 맞는 정보를 가져온다.
#DB에 저장된 가장 최근 정보를 가지고 온도 led의 on, off를 결정한다.
@app.route('/get_device_status', methods=['GET'])
def get_device_status():
    if request.method == 'GET':
        try:
            # block_ip를 GET 파라미터로 받음
            block_Num = request.args.get('block_Num')
        
            with conn.cursor() as cursor:
                
                # 가장 최근의 습도 데이터 조회 -> 건조한 환경에 의한 화재 발생 가능성 탐색
                humi_sql = f"SELECT humi_data FROM T{block_Num} WHERE date_time = (SELECT MAX(date_time) FROM T{block_Num})"
                cursor.execute(humi_sql)
                humi_result = cursor.fetchone()
                #fireNow테이블의 2진수 데이터의 합을 이용하여 화재의 발생과 위치를 조회
                temp_aware_sql = f"SELECT SUM(num) AS num FROM fireNow WHERE switch=true"
                cursor.execute(temp_aware_sql)
                aware_result = cursor.fetchone()
                    
                if humi_result is not None and aware_result is not None:
                    latest_humi = humi_result['humi_data']
                    num = aware_result['num']

                    response = {
                        'temp': '0',
                        'humi': '0',
                        'xyz' : 'dummy'
                    }
                
                    # 데이터를 전송
                    if num is not None:
                        response['temp'] = str(num)# 1 : 01, 2 : 02, 3 : 01&&02, 4 : 03, 5 : 01&&03, 6 : 02&&03, 7 : 01&&02&&03

                    if float(latest_humi) <= 50.0:
                        response['humi'] = '1'

                    return jsonify(response)
                else:
                    return "조회된 데이터가 없습니다."
    
        
        except Exception as e:
            return f"Error: {str(e)}"
    
if __name__ == '__main__':
    app.run(host = "0.0.0.0", port = 5000)
