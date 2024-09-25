# Solar Panel Performance Analysis and Maintenance Platform

## 프로젝트 개요
이 프로젝트는 가정용 태양광 패널의 성능을 분석하고 유지보수 서비스를 제공하는 웹 플랫폼입니다. <br>
사용자는 자신의 발전 데이터를 입력하고, 가까운 공공기관의 태양광 패널 데이터를 비교하여 성능을 평가할 수 있습니다.<br>
이를 통해 패널의 효율 저하 요인을 진단하고, 유지보수 솔루션을 제안합니다.

## 주요 기능

### 1. 사용자 발전량 입력
- 사용자가 가정에 설치한 태양광 패널의 용량 및 당월 발전량을 입력할 수 있습니다.

### 2. 공공기관 패널 데이터 비교
- 사용자의 위치를 기반으로 가까운 공공기관을 찾아 해당 공공기관의 태양광 패널 용량 및 발전량을 분석합니다.

### 3. 발전량 예측
- 공공기관의 기상 데이터(일사량, 기온, 습도 등)를 수집하여, 공공기관 태양광 패널의 용량과 일사량을 연관 지어 발전량을 예측합니다.

### 4. 성능 분석
- 사용자의 발전량과 공공기관의 발전량을 비교하여, 사용자 패널 성능 효율을 분석합니다.

### 5. 유지보수 서비스 제공
- 먼지, 낙엽, 날씨 영향, 파손 등으로 인해 패널 성능이 저하되는 경우, 유지보수 서비스를 제공합니다.

## 기술 스택
- **Frontend**: HTML, CSS, JavaScript
- **Backend**: Python (Django)
- **Database**: MySQL
- **API**: Google Geocoding API
- **Machine Learning**: Random Forest, XGBoost, LightGBM
- **Data Processing**: Pandas, NumPy
- **Visualization**: Folium
