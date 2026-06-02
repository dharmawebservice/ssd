from itertools import product
import json
import random
import re
import requests
from geopy.geocoders import Nominatim
from .models import Category
from .models import Product
from .models import Order
from datetime import timedelta
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.text import slugify
from .models import EmailOTP, Product, UserProfile
from .models import Order
from .models import Coupon
from django.shortcuts import render

from .models import (
    Category,
    Product,
    Banner,
    Review
)


def home(request):

    try:
        categories = Category.objects.filter(
            is_active=True
        ).order_by("-id")

    except Exception:
        categories = []

    try:
        products = Product.objects.filter(
            is_active=True
        ).order_by("-id")[:8]

    except Exception:
        products = []

    try:
        banners = Banner.objects.filter(
            is_active=True
        ).order_by("-id")

    except Exception:
        banners = []

    try:
        reviews = Review.objects.filter(
            is_approved=True
        ).order_by("-id")[:6]

    except Exception:
        reviews = []


    context = {

        "categories": categories,
        "products": products,
        "banners": banners,
        "reviews": reviews,

    }

    return render(
        request,
        "web/home.html",
        context
    )


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


from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login

def login_user(request):

    if request.method == "POST":

        data = json.loads(request.body)

        email_or_username = data.get("email", "").strip()
        password = data.get("password", "").strip()

        user = None

        # Try username login
        user = authenticate(
            request,
            username=email_or_username,
            password=password
        )

        # If not found, try email login
        if not user:
            try:
                db_user = User.objects.get(
                    email=email_or_username
                )

                user = authenticate(
                    request,
                    username=db_user.username,
                    password=password
                )

            except User.DoesNotExist:
                pass

        if user:

            login(request, user)

            if user.is_superuser:

                return JsonResponse({
                    "success": True,
                    "redirect": "/dashboard/"
                })

            return JsonResponse({
                "success": True,
                "redirect": "/"
            })

        return JsonResponse({
            "success": False,
            "message": "Invalid credentials"
        })

    return JsonResponse({
        "success": False
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
    

def reverse_geocode(request):

    lat = request.GET.get("lat")
    lon = request.GET.get("lon")

    try:

        if not lat or not lon:
            return JsonResponse({
                "success": False,
                "message": "Latitude and Longitude are required"
            })

        geolocator = Nominatim(
            user_agent="ssd_nursery"
        )

        location = geolocator.reverse(
            f"{lat}, {lon}",
            exactly_one=True,
            language="en"
        )

        if not location:
            return JsonResponse({
                "success": False,
                "message": "Location not found"
            })

        addr = location.raw.get("address", {})

        print("ADDRESS DATA:", addr)

        area = (
            addr.get("suburb")
            or addr.get("neighbourhood")
            or addr.get("village")
            or addr.get("hamlet")
            or ""
        )

        city = (
            addr.get("city")
            or addr.get("town")
            or addr.get("county")
            or addr.get("municipality")
            or ""
        )

        state = addr.get("state", "")

        pincode = (
            addr.get("postcode")
            or addr.get("postal_code")
            or ""
        )

        return JsonResponse({
            "success": True,
            "address": location.address,
            "area": area,
            "city": city,
            "state": state,
            "pincode": pincode
        })

    except Exception as e:

        print("REVERSE GEOCODE ERROR:", str(e))

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


#----------------admin dashboard----------------------#

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.contrib.auth.models import User

from .models import UserProfile


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from .models import (
    Category,
    Product,
    Order
)


@login_required
def admin_dashboard(request):

    # Only Admin Can Access
    if not request.user.is_superuser:
        return redirect("/")

    total_users = User.objects.count()

    total_categories = Category.objects.count()

    total_products = Product.objects.count()

    total_orders = Order.objects.count()

    pending_orders = Order.objects.filter(
        status="Pending"
    ).count()

    completed_orders = Order.objects.filter(
        status="Delivered"
    ).count()

    total_revenue = sum(
        order.total_amount
        for order in Order.objects.filter(
            status="Delivered"
        )
    )

    recent_orders = Order.objects.select_related(
        "user"
    ).order_by("-id")[:5]

    context = {

        "total_users": total_users,

        "total_categories": total_categories,

        "total_products": total_products,

        "total_orders": total_orders,

        "pending_orders": pending_orders,

        "completed_orders": completed_orders,

        "total_revenue": total_revenue,

        "recent_orders": recent_orders,

    }

    return render(
        request,
        "web/admin/dashboard.html",
        context
    )

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect

from .models import UserProfile


@login_required
def users_list(request):

    if not request.user.is_superuser:
        return redirect("/")

    users = User.objects.select_related(
        "userprofile"
    ).all().order_by("-date_joined")

    return render(
        request,
        "web/admin/users.html",
        {"users": users}
    )

from .models import Category
from django.contrib import messages


@login_required
def category_list(request):

    if not request.user.is_superuser:
        return redirect("/")

    categories = Category.objects.all().order_by("-id")

    return render(
        request,
        "web/admin/categories.html",
        {
            "categories": categories
        }
    )

@login_required
def add_category(request):

    if not request.user.is_superuser:
        return redirect("/")

    if request.method == "POST":

        name = request.POST.get("name")
        description = request.POST.get("description")
        image = request.FILES.get("image")

        if Category.objects.filter(
            name__iexact=name
        ).exists():

            messages.error(
                request,
                "Category already exists"
            )

            return redirect(
                "category_list"
            )

        Category.objects.create(
            name=name,
            description=description,
            image=image
        )

        messages.success(
            request,
            "Category added successfully"
        )

        return redirect(
            "category_list"
        )

    return redirect(
        "category_list"
    )

@login_required
def delete_category(request, id):

    if not request.user.is_superuser:
        return redirect("/")

    category = Category.objects.get(
        id=id
    )

    category.delete()

    messages.success(
        request,
        "Category deleted"
    )

    return redirect(
        "category_list"
    )

@login_required
def product_list(request):

    if not request.user.is_superuser:
        return redirect("/")

    products = Product.objects.select_related(
        "category"
    ).all().order_by("-id")

    return render(
        request,
        "web/admin/products.html",
        {
            "products": products,
            "categories": Category.objects.all()
        }
    )

@login_required
def add_product(request):

    if not request.user.is_superuser:
        return redirect("/")

    if request.method == "POST":

        category_id = request.POST.get(
            "category"
        )

        category = Category.objects.get(
            id=category_id
        )

        name = request.POST.get(
            "name"
        )

        price = request.POST.get(
            "price"
        )

        offer_price = request.POST.get(
            "offer_price"
        )

        stock = request.POST.get(
            "stock"
        )

        description = request.POST.get(
            "description"
        )

        care_guide = request.POST.get(
            "care_guide"
        )

        image = request.FILES.get(
            "image"
        )

        Product.objects.create(
            category=category,
            name=name,
            slug=slugify(name),
            price=price,
            offer_price=offer_price,
            stock=stock,
            description=description,
            care_guide=care_guide,
            image=image
        )

        return redirect(
            "product_list"
        )

    return redirect(
        "product_list"
    )

@login_required
def delete_product(request,id):

    if not request.user.is_superuser:
        return redirect("/")

    Product.objects.filter(
        id=id
    ).delete()

    return redirect(
        "product_list"
    )


@login_required
def order_list(request):

    if not request.user.is_superuser:
        return redirect("/")

    orders = Order.objects.select_related(
        "user"
    ).all().order_by("-id")

    return render(
        request,
        "web/admin/orders.html",
        {
            "orders": orders
        }
    )

@login_required
def update_order_status(
    request,
    order_id
):

    if not request.user.is_superuser:
        return redirect("/")

    order = Order.objects.get(
        id=order_id
    )

    status = request.POST.get(
        "status"
    )

    order.status = status

    order.save()

    return redirect(
        "order_list"
    )

@login_required
def coupon_list(request):

    if not request.user.is_superuser:
        return redirect("/")

    coupons = Coupon.objects.all().order_by("-id")

    return render(
        request,
        "web/admin/coupons.html",
        {
            "coupons": coupons
        }
    )

@login_required
def add_coupon(request):

    if not request.user.is_superuser:
        return redirect("/")

    if request.method == "POST":

        Coupon.objects.create(

            code=request.POST.get(
                "code"
            ).upper(),

            discount_type=request.POST.get(
                "discount_type"
            ),

            discount_value=request.POST.get(
                "discount_value"
            ),

            minimum_order_amount=request.POST.get(
                "minimum_order_amount"
            ),

            maximum_discount=request.POST.get(
                "maximum_discount"
            ),

            expiry_date=request.POST.get(
                "expiry_date"
            )

        )

        return redirect(
            "coupon_list"
        )

    return redirect(
        "coupon_list"
    )

@login_required
def delete_coupon(request,id):

    if not request.user.is_superuser:
        return redirect("/")

    Coupon.objects.filter(
        id=id
    ).delete()

    return redirect(
        "coupon_list"
    )

from .models import Review

@login_required
def reviews_list(request):

    if not request.user.is_superuser:
        return redirect("/")

    reviews = Review.objects.select_related(
        "user",
        "product"
    ).all().order_by("-id")

    return render(
        request,
        "web/admin/reviews.html",
        {
            "reviews": reviews
        }
    )


@login_required
def approve_review(request,id):

    review = Review.objects.get(id=id)

    review.is_approved = True

    review.save()

    return redirect("reviews_list")


@login_required
def delete_review(request,id):

    Review.objects.filter(id=id).delete()

    return redirect("reviews_list")

from .models import Banner

@login_required
def banners_list(request):

    banners = Banner.objects.all()

    return render(
        request,
        "web/admin/banners.html",
        {
            "banners": banners
        }
    )


@login_required
def add_banner(request):

    if request.method == "POST":

        Banner.objects.create(

            title=request.POST.get(
                "title"
            ),

            banner_type=request.POST.get(
                "banner_type"
            ),

            image=request.FILES.get(
                "image"
            )

        )

        return redirect(
            "banners_list"
        )

    return redirect(
        "banners_list"
    )


@login_required
def delete_banner(request,id):

    Banner.objects.filter(
        id=id
    ).delete()

    return redirect(
        "banners_list"
    )

from django.db.models import Sum

@login_required
def analytics(request):

    total_users = User.objects.count()

    total_products = Product.objects.count()

    total_orders = Order.objects.count()

    total_revenue = Order.objects.filter(
        status="Delivered"
    ).aggregate(
        Sum("total_amount")
    )["total_amount__sum"] or 0

    return render(
        request,
        "web/admin/analytics.html",
        {
            "total_users": total_users,
            "total_products": total_products,
            "total_orders": total_orders,
            "total_revenue": total_revenue
        }
    )

