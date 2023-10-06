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
                            password='1234', # MySQL 비밀번호
                            db='testdb', # MySQL 스키마 이름
                            charset='utf8mb4',
                            cursorclass=pymysql.cursors.DictCursor)

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
            try:
                with conn.cursor() as cursor:
                    # 테이블 생성
                        create_table_sql = f"CREATE TABLE IF NOT EXISTS T{block_ip} (date_time DATETIME PRIMARY KEY DEFAULT CURRENT_TIMESTAMP, temp_data FLOAT NOT NULL, humi_data FLOAT NOT NULL)"
                        cursor.execute(create_table_sql)
                    #평균집계 테이블 생성
                        create_table_avg_sql = f"CREATE TABLE IF NOT EXISTS T1{block_ip} (hour_date_time DATETIME PRIMARY KEY , avg_temp_data FLOAT NOT NULL, avg_humi_data FLOAT NOT NULL)"
                        cursor.execute(create_table_avg_sql)
                        
                    # 데이터 삽입
                        insert_data_sql = f"INSERT INTO T{block_ip} (temp_data, humi_data) VALUES ({temp_data}, {humi_data})"
                        cursor.execute(insert_data_sql)

                    # 시간별 데이터 평균화/자동집계
                def automatic_counting():
                        insert_avg_data_sql = f"""
                            INSERT IGNORE INTO T1{block_ip} (hour_date_time, avg_temp_data, avg_humi_data)
                            SELECT
                                DATE_FORMAT(date_time, '%Y-%m-%d %H:00:00'),
                                AVG(temp_data) AS avg_temp_data,
                                AVG(humi_data) AS avg_humi_data
                            FROM T{block_ip}
                            GROUP BY DATE_FORMAT(date_time, '%Y-%m-%d %H:00:00')
                            ON DUPLICATE KEY UPDATE
                             hour_date_time = hour_date_time;    #중복 키가 발생할 경우 아무 작업도 수행X
                        """
                        cursor.execute(insert_avg_data_sql)
                
                # 1시간 뒤부터 실행
                schedule.every(1).hour.at(":00").do(automatic_counting)
                schedule.run_pending()
                #이 후 매 시간마다 automatic_counting 실행
                #schedule.every().hour.do(automatic_counting)
                    
                        
            finally:
                conn.commit()

#get을 통해 디바이스의 ip주소를 받고 이를 이용해 디바이스에 맞는 정보를 가져온다.
#DB에 저장된 가장 최근 정보를 가지고 온도 led의 on, off를 결정한다.
@app.route('/get_device_status', methods=['GET'])
def get_device_status():   
    try:
    # block_ip를 GET 파라미터로 받음
        block_ip = request.args.get('block_ip')
        
        with conn.cursor() as cursor:
            # 가장 최근의 온도 데이터 조회
            temp_sql = f"SELECT temp_data FROM T{block_ip} WHERE date_time = (SELECT MAX(date_time) FROM T{block_ip})"
            cursor.execute(temp_sql)
            temp_result = cursor.fetchone()
            
            # 가장 최근의 습도 데이터 조회
            humi_sql = f"SELECT humi_data FROM T{block_ip} WHERE date_time = (SELECT MAX(date_time) FROM T{block_ip})"
            cursor.execute(humi_sql)
            humi_result = cursor.fetchone()
            
            if temp_result is not None and humi_result is not None:
                latest_temp = temp_result['temp_data']
                latest_humi = humi_result['humi_data']

                fire_awareness_sql = f"UPDATE fireNow SET switch=false WHERE name='temp'"
                if latest_temp >= 30.0:
                    fire_awareness_sql = f"UPDATE fireNow SET switch=true WHERE name='temp'"

                cursor.execute(fire_awareness_sql)
                #----------------------------------

                response = {
                    'ave_temp': 'TEMP_LED_OFF',
                    'ave_humi': 'HUMI_LED_OFF'
                }
                
            # 데이터를 전송
                temp_aware_sql = f"SELECT switch FROM fireNow WHERE name='temp'"
                cursor.execute(temp_aware_sql)
                aware_result = cursor.fetchone()
                if aware_result is not None:
                    switch = aware_result['switch']
                    if switch == 1:
                        response['ave_temp'] = 'TEMP_LED_ON!'

                if latest_humi <= 50.0:
                    response['ave_humi'] = 'HUMI_LED_ON!'

                return jsonify(response)
            else:
                return "조회된 데이터가 없습니다."
    
    except Exception as e:
        return f"Error: {str(e)}"
    
if __name__ == '__main__':
    app.run(host = "0.0.0.0", port = 5000)
