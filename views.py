# 데이터분석
from django.shortcuts import render
from .analysis.map_result import run_analysis, power_analysis, haversine
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.views import PasswordResetDoneView
from datetime import date
from django.utils.dateparse import parse_date
import json
from django.core.exceptions import ObjectDoesNotExist

# 월 별 전력사용량 막대그래프
def graph_analysis(address): # 좌표를 받아
    import pandas as pd
        
    power_usage = pd.read_csv("media/진짜전력사용량.csv")
    # 로그인 안 한 경우 나오게 하는 그래프
    if address == '전국' :
        monthly_avg_usage = power_usage.groupby('month')['powerUsage'].mean().reset_index()
        return monthly_avg_usage['powerUsage'].values
    # 로그인 한 경우 그래프
    else :
        target_lat,target_lon = address
        power_usage['distance'] = power_usage.apply(lambda row: haversine(target_lat, target_lon, row['latitude'], row['longitude']), axis=1)
        closest_region = power_usage.loc[power_usage['distance'].idxmin()]
        # 사용자 패널 주소 지역
        data = power_usage[power_usage['metro'].str.contains(closest_region['metro'])]
        # 월 별 전력 사용량 막대그래프
        monthly_avg_usage = data.groupby('month')['powerUsage'].mean().reset_index()
        return monthly_avg_usage['powerUsage'].values

## 메인페이지
def main_view(request):
    form = LoginForm()
    
    if request.user.is_authenticated:
        Signup_Id = SignUp_User.objects.get(UserId=request.user).id
        
        # Panel 객체가 존재하는지 확인
        panel = Panel.objects.filter(user_id=Signup_Id,state=1).first()
        
        if panel:
            Panel_Id = panel.id
            Location_id = Location.objects.get(user_id=Panel_Id).latitude,Location.objects.get(user_id=Panel_Id).longitude
            capacity = Panel.objects.get(user_id=Signup_Id,state=1).capacity
            # 데이터 분석 함수 호출
            result, top_5_facilities = run_analysis(Location_id)
            
            # 데이터 가공
            capacity = [i for i in top_5_facilities.capacity]
            address = [i for i in top_5_facilities.address]
            latitude = [i for i in top_5_facilities.latitude]
            longitude = [i for i in top_5_facilities.longitude]
            distance = [i for i in top_5_facilities.distance]
            
            # 그래프 시각화
            graph = graph_analysis(Location_id)
        
            # graph 데이터를 JSON으로 변환
            graph_json = json.dumps(list(graph))

            
            return render(request, 'asd/main/basic/main.html', {
                'form': form,
                'result': result,
                'top_5_facilities': top_5_facilities,
                'capacity': capacity,
                'address': address,
                'latitude': latitude,
                'longitude': longitude,
                'distance': distance,
                'graph':graph_json
            })

    # 로그인 안 한 경우 나올 그래프
    graph = graph_analysis('전국')
        
    # graph 데이터를 JSON으로 변환
    graph_json = json.dumps(list(graph))

    # Panel 객체가 없거나 인증되지 않은 경우
    return render(request, 'asd/main/basic/main.html', {'form': form,'graph':graph_json})


# 주소를 위도 및 경도로 변환하고 데이터베이스에 저장하는 뷰 함수
from django.shortcuts import render, redirect
from .models import Location
import requests

# Google Geocoding API Key
API_KEY = 'AIzaSyA4YgP4B-gZQLGg51u6puyDvWXr6oi1eJY'
base_url = 'https://maps.googleapis.com/maps/api/geocode/json'

# 주소를 위도 및 경도로 변환하고 데이터베이스에 저장하는 뷰 함수
def add_location(request):
    if request.method == 'POST':
        panel_id = request.POST.get('panel_id')
        panel = Panel.objects.get(id=panel_id)
        address = panel.location

        # Google Geocoding API를 호출하여 주소를 위도와 경도로 변환
        params = {
            'address': address,
            'key': API_KEY
        }
        response = requests.get(base_url, params=params)
        
        if response.status_code == 200:
            results = response.json()
            if results['status'] == 'OK':
                location_data = results['results'][0]['geometry']['location']
                latitude = location_data['lat']
                longitude = location_data['lng']
                
                # 변환된 위도 및 경도를 Location 모델에 저장
                location = Location(address=address, latitude=latitude, longitude=longitude)
                location.save()
                return redirect('성공')  # 성공 후 리디렉션
            else:
                # API 호출이 성공하지 않았을 때
                print(f"Geocoding failed with status: {results['status']}")
        else:
            # 요청 실패 처리
            print(f"Failed to fetch data from Geocoding API, status code: {response.status_code}")

    return render(request, 'asd/mypage/panel/add_location.html')  # GET 요청 시 입력 폼 페이지를 렌더링

def location_success(request):
    return render(request, 'asd/mypage/panel/location_success.html')  # GET 요청 시 입력 폼 페이지를 렌더링


# 유지보수 서비스
def repair_service_view(request):
    return render(request, 'asd/repair_service.html')


# 유지보수 결과 출력
def repair_service_result(request):
    try:
        signup_user = SignUp_User.objects.get(UserId=request.user)
        panel = Panel.objects.filter(user_id=signup_user.id).first()

        if not panel:
            return render(request, 'asd/repair_service.html', {
                'error_message': '패널 정보가 존재하지 않습니다.',
                'results_available': False,  # Set results_available to False
            })

        panel_capacity = panel.capacity  # 사용자 패널 용량

        if request.method == "POST":
            try:
                user_power = float(request.POST.get('power', 0))  # POST 요청에서 잉여량을 가져옴
                month = int(request.POST.get('month', 1))  # POST 요청에서 월 데이터를 가져옴
            except ValueError:
                return render(request, 'asd/repair_service.html', {
                    'error_message': '입력값이 올바르지 않습니다.',
                    'results_available': False,  # Set results_available to False
                })

            # 패널 위치 정보 가져오기
            location = Location.objects.filter(user_id=panel.id).first()
            location_lat, location_long = (0, 0) if not location else (location.latitude, location.longitude)
            
            energy, power = power_analysis((location_lat, location_long), month, panel_capacity)

            # 잉여량 차이 계산 및 진단명
            if power is not None:
                facility_power = power  # 발전소 잉여량
                if facility_power > 0:
                    power_difference_percent = ((facility_power - user_power) / facility_power) * 100
                else:
                    power_difference_percent = 0

                if power_difference_percent >= 100:
                    status = '고장, 불량'
                elif 35 <= power_difference_percent < 100:
                    status = '파손 의심'
                elif 15 <= power_difference_percent < 35:
                    status = '먼지, 낙엽'
                else:
                    status = '정상'
            else:
                status = '데이터 없음'
            
            return render(request, 'asd/repair_service.html', {
                'panel_capacity': panel_capacity,
                'user_power': user_power,
                'month': month,
                'power': int(power),
                'status': status,
                'results_available': True,  # Set results_available to True
            })

        return render(request, 'asd/repair_service.html', {
            'panel_capacity': panel_capacity,
            'results_available': False,  # Set results_available to False
        })

    except ObjectDoesNotExist:
        return render(request, 'asd/repair_service.html', {
            'error_message': '패널 정보가 존재하지 않습니다.',
            'results_available': False,  # Set results_available to False
        })



def main_panel(request,panel_id):
    if request.method == "POST":
        main_panel_state = request.POST.get('state')
        Signup_Id = SignUp_User.objects.get(UserId=request.user).id
        Panel.objects.filter(user_id=Signup_Id).update(state=0)
        Panel.objects.filter(user_id=Signup_Id,id=panel_id).update(state=1)
    return redirect('패널정보 조회')
