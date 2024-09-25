from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from asd.forms import LoginForm, PanelForm
from .models import Panel
from .forms import SignUpForm,LoginForm
from .models import SignUp_User
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from django.contrib.auth import logout as auth_logout
from .forms import ModifyUserForm
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import check_password
#---------------------------------------------------------------
# 비밀번호 찾기
from django.contrib.auth.views import PasswordResetView
from django.urls import reverse_lazy
from .forms import CustomPasswordResetForm
from .forms import PasswordResetForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.core.mail import send_mail
#---------------------------------------------------------------
# 데이터분석
from django.shortcuts import render
from .analysis.map_result import run_analysis, power_analysis, haversine
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.views import PasswordResetDoneView
from datetime import date
from django.utils.dateparse import parse_date
import json
from django.core.exceptions import ObjectDoesNotExist

## ------------그래프 시각화 함수(graph_analysis) 추가

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

## 메인페이지 - 상단 (목록)
def main_list_1_view(request):
    return render(request, 'asd/main/list/main_list_1.html')  # 메인 목록1
def main_list_2_view(request):
    return render(request, 'asd/main/list/main_list_2.html')  # 메인 목록2
def main_list_3_view(request):
    return render(request, 'asd/main/list/main_list_3.html')  # 메인 목록3
def main_list_4_view(request):
    return render(request, 'asd/main/list/main_list_4.html')  # 메인 목록4
def main_list_5_view(request):
    return render(request, 'asd/main/list/main_list_5.html')  # 메인 목록5

## 즐겨찾기
def bookmark_1_view(request):
    return render(request, 'asd/main/bookmark/bookmark_1.html')  # 즐겨찾기 1
def bookmark_2_view(request):
    return render(request, 'asd/main/bookmark/bookmark_2.html')  # 즐겨찾기 2
def bookmark_3_view(request):
    return render(request, 'asd/main/bookmark/bookmark_3.html')  # 즐겨찾기 3

## 바로가기
# @2024-09-07수정 - 노광우 ----------------------------------
def mypage_view(request):
    user = request.user
    panel = Panel.objects.filter(user=user).first()  # 사용자에 대한 패널 정보를 가져옵니다.
    return render(request, 'asd/mypage/mypage.html', {'panel': panel})

def quick_recent_view(request):  # 최근접속 
    return render(request, 'asd/main/basic/main_recent.html')
def quick_contact_view(request):  # 문의방법
    return render(request, 'asd/main/basic/main_contact.html')

## 메인페이지 - 하단 (정보)
def down_privacy_view(request):  # 개인정보 처리방침        
    return render(request, 'asd/main/down/down_privacy.html')
def down_terms_view(request):  # 이용약관         
    return render(request, 'asd/main/down/down_terms.html')
def down_sitemap_view(request):  # 사이트맵        
    return render(request, 'asd/main/down/down_sitemap.html')

#---------------------------------------------------------------

## 회원가입
# 회원가입 창
#def signup_view(request):
#    return render(request, 'asd/user/basic/signup.html')

#---------------------------------------------------------------

## 로그인
@csrf_exempt
def login_view(request):
    if request.user.is_authenticated:
        logout(request)
        return redirect('로그인')

    if request.method == 'POST':
        username = request.POST.get('UserId')
        password = request.POST.get('UserPassword')

        if not username or not password:
            error_message = '아이디와 비밀번호를 모두 입력해 주세요.'
            return render(request, 'asd/user/basic/login.html', {'error_message': error_message})

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('메인페이지')
        else:
            error_message = '아이디 또는 비밀번호가 올바르지 않습니다.'
            return render(request, 'asd/user/basic/login.html', {'error_message': error_message})

    else:
        return render(request, 'asd/user/basic/login.html')

## 회원정보 찾기
def find_view(request):  # 회원정보 찾기
    return render(request, 'asd/user/find/find.html')
def find_id_view(request):  # 아이디 찾기
    return render(request, 'asd/user/find/find_id.html')
def find_pw_view(request):  # 비밀번호 찾기
    return render(request, 'asd/user/find/find_pw.html')

#---------------------------------------------------------------

## 마이페이지

## 마이페이지 홈
@login_required
def mypage_view(request):
    if not request.user.is_authenticated:
        return redirect('login')  # 로그인 페이지로 리다이렉트
    return render(request, 'asd/mypage/mypage.html')

## 마이페이지 - 회원
# 회원정보 조회 
# @2024-09-07수정 - 노광우 ----------------------------------
@login_required
def search_user_view(request):
    # Retrieve the currently logged-in user
    user = request.user
    
    # Pass the user object to the template
    context = {'user': user}
    return render(request, 'asd/mypage/user/search_user.html', context)

# 회원정보 수정 - 본인확인(비밀번호 입력)
@login_required
def confirm_pw_user_view(request):
    return render(request, 'asd/mypage/user/confirm_pw_user.html')

# 회원정보 수정 - 수정 페이지     
# @2024-09-07수정 - 노광우 ----------------------------------------------
@login_required
def modify_user_view(request):
    user = request.user
    if request.method == 'POST':
        form = ModifyUserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('회원정보조회')  # 수정 후 회원 정보 조회 페이지로 리다이렉트
    else:
        form = ModifyUserForm(instance=user)

    return render(request, 'asd/mypage/user/modify_user.html', {'form': form})


## 마이페이지 - 패널

# 패널정보조회
# @2024-09-08 수정 - 노광우 --------------------------------------------
@login_required
def search_panel_view(request):
    user = request.user  # 현재 로그인된 사용자
    panels = Panel.objects.filter(user=user)  # 해당 사용자의 패널 정보 조회
    return render(request, 'asd/mypage/panel/search_panel.html', {'panels': panels})

# 패널정보 수정
def modify_panel_view(request, panel_id):
    # 패널 객체를 가져옵니다. 만약 패널이 존재하지 않으면 404 에러를 발생시킵니다.
    panel = get_object_or_404(Panel, pk=panel_id)
    
    if request.method == 'POST':
        form = PanelForm(request.POST, instance=panel)
        if form.is_valid():
            form.save()
            location_value = form.cleaned_data.get('location')
            modify_location(location_value,panel_id)
            # 수정 완료 후 적절한 페이지로 리다이렉트할 수 있습니다.
            return redirect('패널정보 조회')  # 예를 들어, 패널 정보 조회 페이지로 리다이렉트
    else:
        form = PanelForm(instance=panel)
    
    return render(request, 'asd/mypage/panel/modify_panel.html', {'form': form, 'panel': panel})

#패널정보삭제
def delete_panel_view(request, panel_id):
    if request.method == 'POST':
        panel = get_object_or_404(Panel, id=panel_id, user=request.user)
        panel_id = Panel.objects.get(id=panel_id, user=request.user).id
        Location_id = Location.objects.get(user_id=panel_id)
        panel.delete()
        Location_id.delete()
        return redirect('패널정보 조회')  # 삭제 후 리다이렉트할 URL
    else:
        return HttpResponseForbidden("이 페이지를 볼 수 없습니다.")  
#---------------------------------------------------------------


# 2024-09-07추가 --------------------------------------노광우------------------------------


# 회원가입
def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.UserPassword = make_password(form.cleaned_data['UserPassword'])
            user.save()
            messages.success(request, '회원가입이 완료되었습니다. 로그인 페이지로 이동합니다.')
            return redirect('로그인')  # 로그인 페이지로 리다이렉트
    else:
        form = SignUpForm()

    return render(request, 'asd/user/basic/signup.html', {'form': form})



# 로그아웃

def logout_view(request):
    auth_logout(request)  # Django의 logout 함수 사용
    return redirect('메인페이지')  # 로그아웃 후 메인 페이지로 리디렉션


# 아이디 중복확인
def check_id_duplicate(request):
    user_id = request.GET.get('UserId', '')
    exists = SignUp_User.objects.filter(UserId=user_id).exists()
    return JsonResponse({'exists': exists})

# 이메일 중복확인
def check_email_duplicate(request):
    user_email = request.GET.get('UserEmail', '')
    exists = SignUp_User.objects.filter(UserEmail=user_email).exists()
    return JsonResponse({'exists': exists})

# 회원정보 수정시 비밀번호 확인페이지
def confirm_pw_user_view(request):
    return render(request, 'asd/mypage/user/confirm_pw_user.html')

# 회원정보 수정시 비밀번호 확인
@csrf_exempt
@login_required
def validate_password(request):
    if request.method == 'POST':
        input_password = request.POST.get('UserPassword')
        user = request.user  # 현재 로그인한 사용자 가져오기
        
        if check_password(input_password, user.UserPassword):
            return JsonResponse({'valid': True})
        else:
            return JsonResponse({'valid': False})
    
    return JsonResponse({'valid': False}, status=400)

# 패널 정보 입력
@login_required
def input_panel_view(request):
    user = request.user
    panel_exists = Panel.objects.filter(user=user).exists()

    if request.method == 'POST':
        form = PanelForm(request.POST)
        if form.is_valid():
            panel = form.save(commit=False)
            panel.user = user
            panel.save()
            return redirect('search_panel')
    else:
        form = PanelForm()

    return render(request, 'asd/mypage/panel/input_panel.html', {'form': form})

# 패널 정보 저장
@login_required  # 사용자 인증 확인
def save_panel_view(request):
    if request.method == 'POST':
        form = PanelForm(request.POST)
        if form.is_valid():
            panel = form.save(commit=False)
            panel.user = request.user  # 현재 로그인한 사용자와 연결
            location_value = form.cleaned_data.get('location')
            Signup_Id = SignUp_User.objects.get(UserId=panel.user).id
            panel.save()
            input_location(location_value,panel.id)
            messages.success(request, '패널 정보가 성공적으로 입력되었습니다.')  # 성공 메시지 추가
            return redirect('패널정보 조회')
    else:
        form = PanelForm()
    return render(request, 'asd/mypage/panel/input_panel.html', {'form': form})

def modify_location(location,panel_id):
        params = {
            'address': location,
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
                if Location.objects.filter(user_id=panel_id):
                   Location.objects.filter(user_id=panel_id).update(address=location, latitude=latitude, longitude=longitude,user_id=panel_id)
                else:
                    location = Location(address=location, latitude=latitude, longitude=longitude,user_id=panel_id)
                    location.save()

            else:
                # API 호출이 성공하지 않았을 때
                print(f"Geocoding failed with status: {results['status']}")
        else:
            # 요청 실패 처리
            print(f"Failed to fetch data from Geocoding API, status code: {response.status_code}")

def input_location(location,panel_id):
        params = {
            'address': location,
            'key': API_KEY
        }
        response = requests.get(base_url, params=params)
        if response.status_code == 200:
            results = response.json()
            if results['status'] == 'OK':
                location_data = results['results'][0]['geometry']['location']
                latitude = location_data['lat']
                longitude = location_data['lng']

                location = Location(address=location, latitude=latitude, longitude=longitude,user_id=panel_id)
                location.save()

    

# # 패널정보 수정
# @login_required
# def modify_panel_view(request, panel_id):
#     today = date.today()
#     panel = Panel.objects.get(id=panel_id)

#     if request.method == 'POST':
#         form = PanelForm(request.POST, instance=panel)
#         if form.is_valid():
#             # 서버 측 유효성 검사
#             cleaned_data = form.cleaned_data
#             if cleaned_data['date'] > today:
#                 form.add_error('date', '설치일자는 오늘 이후의 날짜로 설정할 수 없습니다.')
#             if cleaned_data['record'] > today:
#                 form.add_error('record', '점검기록일자는 오늘 이후의 날짜로 설정할 수 없습니다.')
            
#             if not form.errors:
#                 form.save()
#                 return redirect('패널정보 조회')  # 성공적으로 저장되면 페이지 이동
#     else:
#         form = PanelForm(instance=panel)

#     context = {
#         'form': form,
#         'today': today
#     }
#     return render(request, 'asd/mypage/panel/modify_panel.html', context)
# 2024-09-07추가 --------------------------------------노광우------------------------------


#-------------------------------------------------------09.09 동연 추가
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


# 비밀번호 찾기 --------------------------------------------

# 비밀번호 재설정시 이메일에 따라 로그인창 띄우기
class CustomPasswordResetView(PasswordResetView):
    form_class = CustomPasswordResetForm
    email_template_name = 'registration/password_reset_email.html'
    subject_template_name = 'registration/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')

    def form_valid(self, form):
        response = super().form_valid(form)
        # 이메일을 세션에 저장
        email = form.cleaned_data.get('email')
        self.request.session['reset_email'] = email
        return response


# 비밀번호 재설정 커스텀 페이지(password_reset_confirm.html)
def password_reset_confirm_view(request, uidb64=None, token=None):
    User = get_user_model()
    if request.method == 'POST':
        form = SetPasswordForm(user=User.objects.get(pk=uidb64), data=request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            return redirect('password_reset_complete')
    else:
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
            form = SetPasswordForm(user=user)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
            form = SetPasswordForm(user=None)
    
    return render(request, 'password_reset_confirm.html', {'form': form})


# 아이디 찾기
User = get_user_model()

def find_id_view(request):
    found_id = None
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        
        if not name or not email:
            messages.error(request, '이름과 이메일을 모두 입력해주세요.')
            return redirect('find_id')

        try:
            user = User.objects.get(UserName=name, UserEmail=email)
            found_id = user.UserId  # 찾은 아이디 저장
        except User.DoesNotExist:
            messages.error(request, '입력하신 정보와 일치하는 아이디를 찾을 수 없습니다.')
            return redirect('find_id')
    
    return render(request, 'asd/user/find/find_id.html', {'found_id': found_id})

# # 데이터분석
# def map_result(request):
#     Signup_Id = SignUp_User.objects.get(UserId=request.user).id
#     Panel_Id = Panel.objects.filter(user_id=Signup_Id).first().id
#     Location_id = Location.objects.get(user_id=Panel_Id).address
    
#     # result = run_analysis(Location_id)  # 데이터 분석 함수 호출
#     # return render(request, 'asd/map_result.html', {'result': result})

#     result,top_5_facilities = run_analysis(Location_id)  # 지도 HTML 및 분석 결과 반환
#     return render(request, 'asd/map_result.html', {'result': result,"top_5_facilities":top_5_facilities})



# 비밀번호 재설정시 로그인
class CustomPasswordResetDoneView(PasswordResetDoneView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_email'] = self.request.session.get('reset_email', '')
        return context
    
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

## 공지사항

def main_notice_1_view(request):
    return render(request, 'asd/main/notice/notice1.html') 
def main_notice_2_view(request):
    return render(request, 'asd/main/notice/notice2.html') 
def main_event_1_view(request):
    return render(request, 'asd/main/notice/event1.html') 
def main_event_2_view(request):
    return render(request, 'asd/main/notice/event2.html') 