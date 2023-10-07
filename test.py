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
                            password='hci7712!@!', # MySQL 비밀번호
                            db='fire_iot', # MySQL 스키마 이름
                            charset='utf8mb4',
                            cursorclass=pymysql.cursors.DictCursor)
plz = "00"

def automatic_delete():
    global plz
    delete_data_sql = f"""
    DELETE FROM T{plz}
    WHERE date_time < DATE_SUB(NOW(), INTERVAL 5 MINUTE )"""
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

schedule.every().hour.at(":22").do(automatic_counting) #1시간마다 1번씩 시간 단위 취합.
schedule.every().hour.at(":22").do(automatic_delete)

@app.route('/')
def hello():
    name = request.args.get("name", "World")
    return f'Hello, {escape(name)}!'

@app.route('/process_data', methods=['POST'])
def process_data():
    if request.method == 'POST':
        temp_data = request.form['temp_data']
        humi_data = request.form['humi_data']
        block_ip = request.form['block_ip']

        #------------------------------------
        ji = int(block_ip)
        number = 2*(ji-1) if ji != 1 else 1
        global plz
        plz = str(block_ip)
        #------------------------------------
        
        try:
            with conn.cursor() as cursor:
                # 테이블 생성
                create_table_sql = f"CREATE TABLE IF NOT EXISTS T{block_ip} (date_time DATETIME PRIMARY KEY DEFAULT CURRENT_TIMESTAMP, temp_data FLOAT NOT NULL, humi_data FLOAT NOT NULL)"
                cursor.execute(create_table_sql)
                #평균집계 테이블 생성
                create_table_avg_sql = f"CREATE TABLE IF NOT EXISTS T1{block_ip} (hour_date_time DATETIME PRIMARY KEY , avg_temp_data FLOAT NOT NULL, avg_humi_data FLOAT NOT NULL)"
                cursor.execute(create_table_avg_sql)

                schedule.run_pending() #이전 값 취합과 삭제가 완료된 후 
                
                # 데이터 삽입
                insert_data_sql = f"INSERT INTO T{block_ip} (temp_data, humi_data) VALUES ({temp_data}, {humi_data})"
                cursor.execute(insert_data_sql)

                #fire_awareness_sql = f"UPDATE fireNow SET switch=false WHERE name='temp'"
                fire_awareness_sql = f"INSERT INTO fireNow(name, switch, num) VALUES('T{block_ip}', false, {number}) ON DUPLICATE KEY UPDATE switch=false"
                if float(temp_data) >= 30.0:
                    #fire_awareness_sql = f"UPDATE fireNow SET switch=true WHERE name='temp'"
                    fire_awareness_sql = f"INSERT INTO fireNow(name, switch, num) VALUES('T{block_ip}', true, {number}) ON DUPLICATE KEY UPDATE switch=true"
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
            block_ip = request.args.get('block_ip')
        
            with conn.cursor() as cursor:
                # 가장 최근의 온도 데이터 조회
            
                # 가장 최근의 습도 데이터 조회
                humi_sql = f"SELECT humi_data FROM T{block_ip} WHERE date_time = (SELECT MAX(date_time) FROM T{block_ip})"
                cursor.execute(humi_sql)
                humi_result = cursor.fetchone()

                #temp_aware_sql = f"SELECT switch FROM fireNow WHERE name='temp'"
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
