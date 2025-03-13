from django.shortcuts import render,redirect
from django.contrib import messages
import requests


LOGIN = 'https://piqapi.purpleiq.ai/api/Authentication/Login'

def login_view(request): 
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        payload = {
            "userId": username,
            "password": password
        }
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        try:
            response = requests.post(LOGIN, json=payload, headers=headers, allow_redirects=False)
            response.raise_for_status()  
            data = response.json()
            print('Response data:', data)

            message = data.get('message', 'Unknown Error')

            if message and 'Otp' in message:
                request.session['username'] = username
                request.session['password'] = password
                messages.success(request, 'OTP Received Your EMAIL')
                return redirect('otp')  
            else:
                messages.error(request, f'Error: {message}')
        except requests.RequestException as e:
            print(f"Request Exception: {e}")
            messages.error(request, 'There was an error connecting to the login API.')

    return render(request, 'app1/login.html')

OTP_API = 'https://piqapi.purpleiq.ai/api/Authentication/TwoFactorAuthentication'

def otp_view(request):
    if request.method == 'POST':
        otp = request.POST.get('otp')
        username = request.session.get('username')
        password = request.session.get('password')

        payload = {
            "userId": username,
            "twoAuthCode": otp
        }
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        try:
            response = requests.post(OTP_API, json=payload, headers=headers)
            if response.status_code != 200:
                messages.error(request, f"Error: {response.status_code} - Could not contact the OTP API.")
                return render(request, 'app1/otp.html')
            
            
            try:
                data = response.json()
            except ValueError:
                messages.error(request, "Error: Invalid JSON response from OTP verification API.")
                return render(request, 'app1/otp.html')

            print("OTP response:", data)  

            if data.get('isError'):
                messages.error(request, f"OTP verification failed: {data.get('errorMessage', 'Unknown error')}")
                return render(request, 'app1/otp.html')

            if data.get('message') and 'Login' in data['message']:
                messages.success(request, 'OTP verified successfully.')
                return redirect('emp')

    
            messages.error(request, 'OTP verification failed. Please try again.')

        except requests.RequestException as e:
            messages.error(request, f'An error occurred during OTP verification: {str(e)}')

    return render(request, 'app1/otp.html')

RESEND_OTP_API = 'https://piqapi.purpleiq.ai/api/Authentication/ReSendOtpLogin'

def resend_otp_view(request):
    username = request.session.get('username')  
    if username:
        payload = {"userId": username}
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'text/plain'  
        }

        try:
            response = requests.post(RESEND_OTP_API, json=payload, headers=headers)
            print("API Response Status Code:", response.status_code)
            print("API Response Body:", response.text)
            
            data = response.json() 
            
            if data.get("isError") == False and data.get("statusCode") == 0:
                messages.success(request, data.get("message", "OTP has been resent successfully."))
            else:
                error_message = data.get("errorMessage", "Failed to resend OTP.")
                messages.error(request, f"Failed to resend OTP: {error_message}")
        except requests.RequestException as e:
            messages.error(request, f'An error occurred: {str(e)}')
        except ValueError:
            messages.error(request, "Failed to process the API response.")
    else:
        messages.error(request, 'Session expired or invalid. Please log in again.')

    return redirect('otp')

import requests
from django.shortcuts import render
from django.http import HttpResponse

def employee_info_view(request):
    email = request.session.get('username', 'Guest')
    tenant_id = 'C01'
    payload = {
        "data": {
            "clientId": "C01",
            "userId": email,  
            "pageNumber": 1,
            "pageSize": 36,
            "searchKey": "",
            "projectId": "",
            "countryId": "",
            "areaId": "",
            "buildingId": "",
            "floorId": "",
            "zoneId": "",
            "roleid": "",
            "fromDate": "",
            "toDate": ""
        }
    }

    headers = {
        'Content-Type': 'application/json',
        'Tenant-ID': tenant_id,
    }

    full_response = {} 

    try:
        response = requests.post(
            'https://piqapi.purpleiq.ai/api/administrator/Configuration/Employee/EmployeeSummary',
            headers=headers,
            json=payload
        )

        if response.status_code == 200:
            full_response = response.json()
            employee_data = full_response.get('employees', [])
            print('api response body :', response.text)
            print("Employee Data:", employee_data)
        else:
            print("API Error:", response.status_code, response.text)
            employee_data = []
    
    except requests.RequestException as e:
        print("Request Exception:", e)
        employee_data = []

    return render(request, 'app1/emp.html', {
        'employee_data': employee_data,
        'full_response': full_response,
        'email': email  
    })
import os
import json
import requests
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from django.conf import settings

# Paths
DESKTOP_PATH = os.path.join(settings.BASE_DIR, 'app1', 'static', 'app1','id cards')
FONT_PATH = os.path.join(settings.BASE_DIR, 'app1', 'static', 'app1', 'fonts', 'arial.ttf')
TEMPLATE_PATHS = {
    'type1': os.path.join(settings.BASE_DIR, 'app1', 'static', 'app1','Bahrain Steel Card.PNG'),
    'type2': os.path.join(settings.BASE_DIR, 'app1', 'static', 'app1', 'Contractors Card BS.PNG'),
    'type3': os.path.join(settings.BASE_DIR, 'app1', 'static', 'app1', 'Foulath Infotech Card.PNG'),
    'type4': os.path.join(settings.BASE_DIR, 'app1', 'static', 'app1','SULB Card.PNG'),
}

def fetch_employee_data(employee_id):
    payload = {"data": {"clientId": "C01", "userId": "astil.mathew@gmail.com", "searchKey": employee_id}}
    headers = {'Content-Type': 'application/json', 'Tenant-ID': 'C01'}
    
    try:
        response = requests.post(
            'https://piqapi.purpleiq.ai/api/administrator/Configuration/Employee/EmployeeSummary',
            headers=headers,
            json=payload
        )
        if response.status_code == 200:
            data = response.json()
            return next((emp for emp in data.get('employees', []) if emp['idNumber'] == employee_id), None)
    except requests.RequestException as e:
        print(f"API request failed: {e}")
    return None

@csrf_exempt
def generate_selected_id_cards(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            employee_ids = data.get('employee_ids', [])
            card_type = data.get('card_type', 'type1')  

            if not employee_ids:
                return JsonResponse({'message': 'No employees selected.'}, status=400)

            if not os.path.exists(TEMPLATE_PATHS[card_type]):
                return JsonResponse({'message': f"Template {card_type} not found at {TEMPLATE_PATHS[card_type]}"}, status=400)


            generated_files = []

            for employee_id in employee_ids:
                employee = fetch_employee_data(employee_id)
                if not employee:
                    continue

                id_card = Image.open(TEMPLATE_PATHS[card_type]) 
                draw = ImageDraw.Draw(id_card)
                font = ImageFont.truetype(FONT_PATH, 20)

                if employee.get('employeeImage'): 
                    try:
                        response = requests.get(employee['employeeImage'])
                        if response.status_code == 200:
                            employee_image = Image.open(BytesIO(response.content))
                            employee_image = employee_image.resize((245, 245))
                            id_card.paste(employee_image, (562, 140))  
                    except Exception as e:
                        print(f"Error loading employee image for ID {employee_id}: {e}")

               
                draw.text((210, 175), f"{employee['firstname']} {employee['lastname']}", fill="black", font=font)
                draw.text((210, 230), f"{employee['department']}", fill="black", font=font)
                draw.text((210, 285), f"{employee['idNumber']}", fill="black", font=font)
                draw.text((210, 340), f"{employee['nationalId']}", fill="black", font=font)
                draw.text((210, 390), f"{employee.get('endDate', 'N/A')}", fill="black", font=font)

                output_path = os.path.join(DESKTOP_PATH, f"{employee['idNumber']}_id_card.png")
                id_card.save(output_path)
                generated_files.append(output_path)

            return JsonResponse({'message': 'ID cards generated successfully.', 'files': generated_files})

        except Exception as e:
            print("Error:", e)
            return JsonResponse({'message': 'An error occurred while generating ID cards.'}, status=500)

    return JsonResponse({'message': 'Invalid request method.'}, status=405)
