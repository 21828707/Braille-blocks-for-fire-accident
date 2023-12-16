# Braille-blocks-for-fire-accident

- 대구대학교 팀프로젝트 활동
- 인원 : 이백승, 김성민, 전영욱, 박성윤

## 목차

1. 목적
2. 구성도
3. 사용법
4. 결과물
5. 영향

### 목적

- 화재 유도 블럭[Braille-blocks-for-fire-accident]은 화재 발생 시 안전한 대피 경로를 사용자에게 제공하는 것을 최우선 목적으로 한다.
- 또한, 부가적인 목적으로 화재 발생의 감지와 예방을 위한 기능을 포함하며 시각 장애인 편의시설에 대한 접근성을 높이는 것을 목적으로 한다.

### 구성도

- <아두이노 - 온습도 센서 /  WIFI모듈 / LED>
  온습도 정보를 수집한다.
  WIFI모듈을 통해 HTTP 통신으로 서버와 통신한다.

- <서버 – python / mysql>
  HTTP POST / GET 방식의 접근을 구분하여 작동
  PYMYSQL 패키지를 사용하여 MYSQL접근 및 사용.
![image](https://github.com/21828707/Braille-blocks-for-fire-accident/assets/102271662/ae95ac1d-d4a4-43e7-9ae0-72f0b03ae53c)
