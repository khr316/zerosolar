import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import KFold
from sklearn.ensemble import RandomForestRegressor
from math import radians, cos, sin, sqrt, atan2
import requests
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import root_mean_squared_error
import folium

 # 데이터 로드
facilities_capacity = pd.read_csv("media/설비용량.csv")
power_usage = pd.read_csv("media/진짜전력사용량.csv")
weather_df = pd.read_csv("media/진짜진짜기상.csv")

# 좌표로 거리 찾기 함수 생성
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0  # 지구의 반지름 (킬로미터 단위)
    dlat = radians(lat2 - lat1)  # 위도의 차이를 라디안으로 변환
    dlon = radians(lon2 - lon1)  # 경도의 차이를 라디안으로 변환
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2  
    c = 2 * atan2(sqrt(a), sqrt(1 - a))  # Haversine 공식의 c를 계산
    distance = R * c  # 거리 계산
    return distance

def run_analysis(Location_id):

    user_lat, user_lng = Location_id
    
    # 위도와 경도를 숫자로 변환
    facilities_capacity['latitude'] = pd.to_numeric(facilities_capacity['latitude'], errors='coerce')
    facilities_capacity['longitude'] = pd.to_numeric(facilities_capacity['longitude'], errors='coerce')

    # 중복된 위도와 경도를 가진 행 제거 (첫 번째로 나타난 행만 유지)
    unique_facilities = facilities_capacity.drop_duplicates(subset=['latitude', 'longitude']).copy()

    # 사용자 위치(user_lat, user_lng)가 정의되어 있는 경우
    if user_lat and user_lng:
        # 각 공공시설과 사용자 간의 거리를 계산
        unique_facilities.loc[:, 'distance'] = unique_facilities.apply(
            lambda row: haversine(user_lat, user_lng, row['latitude'], row['longitude']),
            axis=1
        )

        # 거리 기준으로 상위 5개의 가장 가까운 공공시설을 선택
        top_5_facilities = unique_facilities.nsmallest(5, 'distance')

    # 지도 시각화
    lat ,long = float(user_lat), float(user_lng)

    m = folium.Map([lat, long], zoom_start=15, tiles='OpenStreetMap')
    

    for i in top_5_facilities.index:
        sub_lat = top_5_facilities.loc[i, 'latitude']
        sub_long = top_5_facilities.loc[i, 'longitude']
        title = top_5_facilities.loc[i, 'address']

        folium.Marker([sub_lat, sub_long], icon=folium.Icon(color='gray'), tooltip=title).add_to(m)

           
    # 사용자 핑 추가
    folium.Marker([user_lat, user_lng], tooltip='사용자 패널').add_to(m)

    return m._repr_html_(),top_5_facilities



def power_analysis(Location_id,month,user_panel) :
    
    m, top_5_facilities = run_analysis(Location_id)
    
    # 공공시설 5군데의 설비용량과 좌표
    top_5_capacity = top_5_facilities['capacity'].tolist()
    top_5_coords = top_5_facilities[['latitude', 'longitude']].values
    
    # 시간 패턴을 적용하여 일사량 분배
    def apply_solar_pattern_to_total(pattern, total_radiation):
        total_pattern = pattern.sum()
        time_ratios = pattern / total_pattern
        adjusted_pattern = time_ratios * total_radiation
        return adjusted_pattern
    
    # 시간 패턴에 따른 발전량 계산 (패널 효율 제외)
    def calculate_energy_based_on_solar_pattern(total_radiation, installation_capacity, solar_pattern):
        hourly_solar_radiation = apply_solar_pattern_to_total(solar_pattern, total_radiation)
        
        # 발전량 계산 (설비 용량 * 시간대별 일사량)
        energy = (installation_capacity * hourly_solar_radiation * 0.2778).sum()  # MJ -> kWh 변환
        return energy, hourly_solar_radiation.sum()  # 총 일사량과 함께 반환
    
    # 날짜별로 가장 가까운 기상 관측소 찾기
    def find_closest_weather_station(facility_coords, weather_df, date_str):
        daily_data = weather_df[weather_df['일시'].str.startswith(date_str)].copy()
        if daily_data.empty:
            return None
        
        daily_data.loc[:, 'distance'] = daily_data.apply(
            lambda row: haversine(facility_coords[0], facility_coords[1], row['위도'], row['경도']), axis=1
        )
        
        return daily_data.loc[daily_data['distance'].idxmin()]
    
    # 환경 요인 보정 계수 적용
    def apply_environmental_factors(weather_data):
        temperature_factor = 1 + (0.32 * (weather_data['평균기온(°C)'] / 100))
        wind_speed_factor = 1 + (0.55 * (weather_data['평균 풍속(m/s)'] / 10))
        humidity_factor = 1 - (0.54 * (weather_data['평균 상대습도(%)'] / 100))
        cloud_factor = 1 - (0.68 * (weather_data['평균 전운량(1/10)'] / 10))
        
        adjustment_factor = temperature_factor * wind_speed_factor * humidity_factor * cloud_factor
        return adjustment_factor
    
    # 환경 요인을 포함한 발전량 예측
    def predict_energy_with_environmental_factors(facility_coords, weather_df, dates, capacities, solar_pattern):
        predictions = []
        
        for i, (coords, capacity) in enumerate(zip(facility_coords, capacities), start=1):
            facility_total_energy = 0
            for date in dates:
                date_str = date.strftime('%Y-%m-%d')
                closest_weather_data = find_closest_weather_station(coords, weather_df, date_str)
                
                if closest_weather_data is not None:
                    total_radiation = closest_weather_data['합계 일사량(MJ/m2)']
                    
                    base_energy, _ = calculate_energy_based_on_solar_pattern(total_radiation, capacity, solar_pattern)
                    adjustment_factor = apply_environmental_factors(closest_weather_data)
                    adjusted_energy = base_energy * adjustment_factor
                    
                else:
                    adjusted_energy = 0
                
                facility_total_energy += adjusted_energy
            
            predictions.append((i, facility_total_energy))
        
        return predictions
    
    # 시간대별 일사량 패턴 정의 (24시간)
    solar_pattern = pd.Series([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.002356, 0.065562, 0.308849, 0.750630, 
                               1.272000, 1.666658, 1.895178, 1.997699, 1.898219, 1.684219, 1.311945, 
                               0.814932, 0.399342, 0.118082, 0.010411, 0.0, 0.0, 0.0], index=range(24))
    
    # 날짜 범위 생성
    def get_days_in_month(month):
        if month in [1, 3, 5, 7, 8, 10, 12]:
            return 31
        elif month in [4, 6, 9, 11]:
            return 30
        elif month == 2:
            return 28

    dates = pd.date_range(f"2024-{month:02d}-01", f"2024-{month:02d}-{get_days_in_month(month)}")
    
    # 환경 요인을 포함한 발전량 예측 수행
    predicted_energy = predict_energy_with_environmental_factors(top_5_coords, weather_df, dates, top_5_capacity, solar_pattern)
    
    
    # 예측 결과 출력
    for facility_num, energy in predicted_energy:
        print(f"공공시설 {facility_num} {month}월 예측 발전량: {energy:.2f}kWh, 설비용량: {top_5_capacity[facility_num-1]}kw")

    # 사용자 패널 용량으로 맞추기
    energy = [energy for energy in predicted_energy]
    
    # 가까운 공공시설들의 패널 용량에 따른 발전량을 
    # 사용자 패널 용량에 맞게 조정
    # 태양광 패널 자가소비율 40% 적용
    # 위 결과가 공공시설의 잉여량이 된다.
    result = [[energy[i][1] for i in range(5)][k]/top_5_capacity[k] for k in range(5)][0] * user_panel * 0.4
    
    return energy,result