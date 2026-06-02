import json
import random
import re
import requests
from geopy.geocoders import Nominatim

from datetime import timedelta
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.core.mail import send_mail
from django.utils import timezone

from .models import EmailOTP, UserProfile


def home(request):
    return render(request, "web/home.html")


def auth_page(request):
    return render(request, "web/auth.html")


def send_signup_otp(request):

    if request.method != "POST":
        return JsonResponse({
            "success": False,
            "message": "Invalid request"
        })

    try:
        data = json.loads(request.body)

        fullname = data.get("fullname", "").strip()
        email = data.get("email", "").strip().lower()
        phone = data.get("phone", "").strip()
        password = data.get("password", "")

        # Full Name Validation
        if len(fullname) < 3:
            return JsonResponse({
                "success": False,
                "message": "Name must contain at least 3 characters"
            })

        if not re.match(r"^[A-Za-z ]+$", fullname):
            return JsonResponse({
                "success": False,
                "message": "Name should contain only letters"
            })

        # Email Validation
        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'

        if not re.match(email_regex, email):
            return JsonResponse({
                "success": False,
                "message": "Enter a valid email address"
            })

        if User.objects.filter(email__iexact=email).exists():
            return JsonResponse({
                "success": False,
                "message": "Email already registered"
            })

        # Phone Validation
        if not phone.isdigit():
            return JsonResponse({
                "success": False,
                "message": "Phone number should contain only digits"
            })

        if len(phone) != 10:
            return JsonResponse({
                "success": False,
                "message": "Phone number must be exactly 10 digits"
            })

        if UserProfile.objects.filter(phone=phone).exists():
            return JsonResponse({
                "success": False,
                "message": "Phone number already registered"
            })

        # Password Validation
        if len(password) < 8:
            return JsonResponse({
                "success": False,
                "message": "Password must be at least 8 characters"
            })

        if not re.search(r"[A-Z]", password):
            return JsonResponse({
                "success": False,
                "message": "Password must contain one uppercase letter"
            })

        if not re.search(r"[a-z]", password):
            return JsonResponse({
                "success": False,
                "message": "Password must contain one lowercase letter"
            })

        if not re.search(r"\d", password):
            return JsonResponse({
                "success": False,
                "message": "Password must contain one number"
            })

        if not re.search(r"[!@#$%^&*()_+=\-{}[\]:;'<>,.?/]", password):
            return JsonResponse({
                "success": False,
                "message": "Password must contain one special character"
            })

        # Generate OTP
        otp = str(random.randint(100000, 999999))

        EmailOTP.objects.update_or_create(
            email=email,
            defaults={"otp": otp}
        )

        request.session["signup_data"] = {
            "fullname": fullname,
            "email": email,
            "phone": phone,
            "password": password
        }
        request.session["verify_email"] = email

        send_mail(
            subject="SSD Nursery Email Verification",
            message=f"""
Hello {fullname},

Your OTP for SSD Nursery account verification is:

{otp}

This OTP is valid for 5 minutes.

Thank You,
SSD Nursery Team
""",
            from_email=None,
            recipient_list=[email]
        )

        return JsonResponse({
            "success": True,
            "message": "OTP sent successfully"
        })

    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": str(e)
        })


def verify_signup_otp(request):

    if request.method != "POST":
        return JsonResponse({
            "success": False,
            "message": "Invalid request"
        })

    try:

        data = json.loads(request.body)

        email = request.session.get("verify_email")
        otp = data.get("otp")

        saved = EmailOTP.objects.get(email=email)

        # OTP Expiry Check
        if timezone.now() - saved.created_at > timedelta(minutes=5):

            saved.delete()

            return JsonResponse({
                "success": False,
                "message": "OTP expired. Please request a new OTP."
            })

        if saved.otp != otp:
            return JsonResponse({
                "success": False,
                "message": "Invalid OTP"
            })

        signup_data = request.session.get("signup_data")

        if not signup_data:
            return JsonResponse({
                "success": False,
                "message": "Session expired. Please signup again."
            })

        if User.objects.filter(email__iexact=email).exists():
            return JsonResponse({
                "success": False,
                "message": "Account already exists"
            })

        user = User.objects.create_user(
            username=email,
            email=email,
            password=signup_data["password"],
            first_name=signup_data["fullname"]
        )

        UserProfile.objects.create(
            user=user,
            phone=signup_data["phone"]
        )

        saved.delete()

        login(request, user)

        return JsonResponse({
            "success": True,
            "message": "OTP Verified Successfully"
        })

    except EmailOTP.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "OTP not found"
        })

    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": str(e)
        })


def login_user(request):

    if request.method != "POST":
        return JsonResponse({
            "success": False,
            "message": "Invalid request"
        })

    try:

        data = json.loads(request.body)

        email = data.get("email", "").strip().lower()
        password = data.get("password", "")

        user = authenticate(
            request,
            username=email,
            password=password
        )

        if not user:
            return JsonResponse({
                "success": False,
                "message": "Invalid email or password"
            })

        login(request, user)

        if user.is_superuser:
            return JsonResponse({
                "success": True,
                "redirect": "/admin/"
            })

        return JsonResponse({
            "success": True,
            "redirect": "/"
        })

    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": str(e)
        })
    
@csrf_exempt
def save_details(request):

    if request.method != "POST":
        return JsonResponse({
            "success": False,
            "message": "Invalid request"
        })

    try:

        if not request.user.is_authenticated:
            return JsonResponse({
                "success": False,
                "message": "Please login first"
            })

        data = json.loads(request.body)

        address = data.get("address", "").strip()
        pincode = data.get("pincode", "").strip()
        instructions = data.get("instructions", "").strip()

        # Address Validation
        if len(address) < 15:
            return JsonResponse({
                "success": False,
                "message": "Address must contain at least 15 characters"
            })

        # Pincode Validation
        if not pincode.isdigit():
            return JsonResponse({
                "success": False,
                "message": "Pincode must contain only digits"
            })

        if len(pincode) != 6:
            return JsonResponse({
                "success": False,
                "message": "Pincode must be exactly 6 digits"
            })

        

        profile = UserProfile.objects.get(
            user=request.user
        )

        profile.address = address
        profile.area = data.get("area", "")
        profile.city = data.get("city", "")
        profile.state = data.get("state", "")
        profile.pincode = pincode
        profile.instructions = instructions

        profile.save()

        return JsonResponse({
            "success": True,
            "message": "Details saved successfully",
            "area": profile.area,
            "city": profile.city,
            "state": profile.state
        })

    except UserProfile.DoesNotExist:

        return JsonResponse({
            "success": False,
            "message": "Profile not found"
        })

    except Exception as e:

        return JsonResponse({
            "success": False,
            "message": str(e)
        })
    
    
def get_location_by_pincode(request):

    pincode = request.GET.get("pincode", "").strip()

    if not pincode:
        return JsonResponse({
            "success": False,
            "message": "Pincode is required"
        })

    if not pincode.isdigit():
        return JsonResponse({
            "success": False,
            "message": "Pincode must contain only digits"
        })

    if len(pincode) != 6:
        return JsonResponse({
            "success": False,
            "message": "Pincode must be exactly 6 digits"
        })

    try:

        response = requests.get(
            f"https://api.postalpincode.in/pincode/{pincode}",
            timeout=10
        )

        data = response.json()

        if (
            not data or
            data[0]["Status"] != "Success" or
            not data[0]["PostOffice"]
        ):
            return JsonResponse({
                "success": False,
                "message": "Invalid pincode"
            })

        office = data[0]["PostOffice"][0]

        return JsonResponse({
            "success": True,
            "area": office.get("Name", ""),
            "city": office.get("District", ""),
            "state": office.get("State", ""),
            "country": office.get("Country", "")
        })

    except Exception as e:

        return JsonResponse({
            "success": False,
            "message": str(e)
        })
    
def reverse_geocode(request):

    lat = request.GET.get("lat")
    lon = request.GET.get("lon")

    try:

        geolocator = Nominatim(
            user_agent="ssd_nursery"
        )

        location = geolocator.reverse(
            f"{lat}, {lon}",
            exactly_one=True
        )

        if not location:
            return JsonResponse({
                "success": False,
                "message": "Location not found"
            })

        addr = location.raw.get("address", {})

        return JsonResponse({
            "success": True,
            "address": location.address,
            "area": (
                addr.get("suburb")
                or addr.get("neighbourhood")
                or addr.get("village")
                or ""
            ),
            "city": (
                addr.get("city")
                or addr.get("town")
                or addr.get("county")
                or ""
            ),
            "state": addr.get("state", ""),
            "pincode": (
                addr.get("postcode")
                or addr.get("postal_code")
                or ""
            )
        })

    except Exception as e:

        return JsonResponse({
            "success": False,
            "message": str(e)
        })
    
def resend_otp(request):

    if request.method != "POST":

        return JsonResponse({
            "success": False,
            "message": "Invalid request"
        })

    try:

        email = request.session.get(
            "verify_email"
        )

        if not email:

            return JsonResponse({
                "success": False,
                "message": "Session expired"
            })

        otp = str(
            random.randint(
                100000,
                999999
            )
        )

        EmailOTP.objects.update_or_create(
            email=email,
            defaults={
                "otp": otp
            }
        )

        send_mail(
            subject="SSD Nursery OTP",
            message=f"Your OTP is {otp}",
            from_email=None,
            recipient_list=[email]
        )

        return JsonResponse({
            "success": True,
            "message": "OTP resent successfully"
        })

    except Exception as e:

        return JsonResponse({
            "success": False,
            "message": str(e)
        })

from django.contrib.auth import logout
from django.shortcuts import redirect


def logout_user(request):

    logout(request)

    return redirect("/")

from django.contrib.auth.decorators import login_required


from django.contrib.auth.decorators import login_required

@login_required
def profile(request):

    profile = UserProfile.objects.get(
        user=request.user
    )

    return render(
        request,
        "web/profile.html",
        {
            "profile": profile
        }
    )