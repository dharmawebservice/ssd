import json
import random
import re
from datetime import timedelta

import requests
from geopy.geocoders import Nominatim

from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.text import slugify
from django.core.paginator import Paginator
from django.db.models import Q, Min, Max, Sum, Avg
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models.functions import TruncMonth

# Import all necessary models
from .models import (
    Category, 
    Product, 
    Banner, 
    Review,
    Order, 
    Coupon, 
    EmailOTP, 
    UserProfile, 
    Notification
)


# ============================================================
# HOME & CORE STORE PAGES
# ============================================================

def shop(request):
    """
    URL params:
      category  — slug of category
      q         — search query
      sort      — price_asc | price_desc | newest | name_asc
      min_price — min price filter
      max_price — max price filter
      sale      — 1  (only offer items)
      in_stock  — 1  (only in-stock items)
      page      — pagination
    """
    products_qs = (
        Product.objects
        .filter(is_active=True)
        .select_related("category")
    )

    # Category filter
    category_slug = request.GET.get("category", "")
    active_category = None
    if category_slug:
        active_category = get_object_or_404(Category, slug=category_slug, is_active=True)
        products_qs = products_qs.filter(category=active_category)

    # Search
    query = request.GET.get("q", "").strip()
    if query:
        products_qs = products_qs.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    # Price range
    price_bounds = Product.objects.filter(is_active=True).aggregate(
        min_p=Min("price"), max_p=Max("price")
    )
    global_min = int(price_bounds["min_p"] or 0)
    global_max = int(price_bounds["max_p"] or 5000)

    min_price = request.GET.get("min_price", "")
    max_price = request.GET.get("max_price", "")
    if min_price.isdigit():
        products_qs = products_qs.filter(price__gte=int(min_price))
    if max_price.isdigit():
        products_qs = products_qs.filter(price__lte=int(max_price))

    # Sale / stock toggle
    if request.GET.get("sale") == "1":
        products_qs = products_qs.exclude(offer_price=None)
    if request.GET.get("in_stock") == "1":
        products_qs = products_qs.filter(stock__gt=0)

    # Sort
    sort = request.GET.get("sort", "newest")
    sort_map = {
        "newest": "-id",
        "price_asc": "price",
        "price_desc": "-price",
        "name_asc": "name",
    }
    products_qs = products_qs.order_by(sort_map.get(sort, "-id"))

    # Pagination
    paginator = Paginator(products_qs, 12)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    # Sidebar data
    categories = Category.objects.filter(is_active=True).order_by("name")

    # Build clean query string without 'page' for pagination links
    query_params = request.GET.copy()
    query_params.pop("page", None)
    filter_string = query_params.urlencode()

    return render(request, "web/shop.html", {
        "page_obj": page_obj,
        "categories": categories,
        "active_category": active_category,
        "query": query,
        "sort": sort,
        "min_price": min_price or global_min,
        "max_price": max_price or global_max,
        "global_min": global_min,
        "global_max": global_max,
        "sale_only": request.GET.get("sale", ""),
        "stock_only": request.GET.get("in_stock", ""),
        "filter_string": filter_string,
        "total_count": paginator.count,
    })


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    reviews = Review.objects.filter(product=product, is_approved=True).select_related("user")
    related = (
        Product.objects
        .filter(category=product.category, is_active=True)
        .exclude(id=product.id)
        .order_by("-id")[:4]
    )
    avg_rating = reviews.aggregate(avg=Avg("rating"))["avg"] or 0
    
    user_review = None
    if request.user.is_authenticated:
        user_review = Review.objects.filter(product=product, user=request.user).first()

    return render(request, "web/product_detail.html", {
        "product": product,
        "reviews": reviews,
        "related": related,
        "avg_rating": round(avg_rating, 1),
        "user_review": user_review,
    })


@login_required
def submit_review(request, product_id):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid request"})
    try:
        product = get_object_or_404(Product, id=product_id)
        data = json.loads(request.body)
        rating = int(data.get("rating", 5))
        review_text = data.get("review", "").strip()
        
        if not review_text or len(review_text) < 10:
            return JsonResponse({"success": False, "message": "Review too short (min 10 chars)"})
            
        Review.objects.update_or_create(
            product=product, 
            user=request.user,
            defaults={
                "rating": rating, 
                "review": review_text, 
                "is_approved": False
            }
        )
        return JsonResponse({"success": True, "message": "Review submitted for approval!"})
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)})


# ============================================================
# AUTHENTICATION & USER PROFILE
# ============================================================

def auth_page(request):
    return render(request, "web/auth.html")


def send_signup_otp(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid request"})
    try:
        data = json.loads(request.body)
        fullname = data.get("fullname", "").strip()
        email = data.get("email", "").strip().lower()
        phone = data.get("phone", "").strip()
        password = data.get("password", "")

        # Validations
        if len(fullname) < 3:
            return JsonResponse({"success": False, "message": "Name must be at least 3 characters"})
        if not re.match(r"^[A-Za-z ]+$", fullname):
            return JsonResponse({"success": False, "message": "Name should contain only letters"})
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            return JsonResponse({"success": False, "message": "Enter a valid email address"})
        if User.objects.filter(email__iexact=email).exists():
            return JsonResponse({"success": False, "message": "Email already registered"})
        if not phone.isdigit() or len(phone) != 10:
            return JsonResponse({"success": False, "message": "Phone number must be exactly 10 digits"})
        if UserProfile.objects.filter(phone=phone).exists():
            return JsonResponse({"success": False, "message": "Phone number already registered"})
        if len(password) < 8:
            return JsonResponse({"success": False, "message": "Password must be at least 8 characters"})
        if not re.search(r"[A-Z]", password):
            return JsonResponse({"success": False, "message": "Password must contain one uppercase letter"})
        if not re.search(r"[a-z]", password):
            return JsonResponse({"success": False, "message": "Password must contain one lowercase letter"})
        if not re.search(r"\d", password):
            return JsonResponse({"success": False, "message": "Password must contain one number"})
        if not re.search(r"[!@#$%^&*()_+=\-{}[\]:;'<>,.?/]", password):
            return JsonResponse({"success": False, "message": "Password must contain one special character"})

        otp = str(random.randint(100000, 999999))
        EmailOTP.objects.filter(
            email=email
        ).delete()

        EmailOTP.objects.create(
            email=email,
            otp=otp
        )
        
        request.session["signup_data"] = {
            "fullname": fullname, "email": email, "phone": phone, "password": password
        }
        request.session["verify_email"] = email

        send_mail(
            subject="SSD Nursery Email Verification",
            message=f"Hello {fullname},\n\nYour OTP is: {otp}\n\nValid for 5 minutes.\n\nSSD Nursery Team",
            from_email=None,
            recipient_list=[email]
        )
        return JsonResponse({"success": True, "message": "OTP sent successfully"})
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)})


def verify_signup_otp(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid request"})
    try:
        data = json.loads(request.body)
        email = request.session.get("verify_email")
        otp = data.get("otp")
        saved = EmailOTP.objects.get(email=email)

        if timezone.now() - saved.created_at > timedelta(minutes=5):
            saved.delete()
            request.session.pop("signup_data", None)
            request.session.pop("verify_email", None)
            return JsonResponse({"success": False, "message": "OTP expired. Please request a new one."})
            
        if saved.otp != otp:
            return JsonResponse({"success": False, "message": "Invalid OTP"})

        signup_data = request.session.get("signup_data")
        if not signup_data:
            return JsonResponse({"success": False, "message": "Session expired. Please sign up again."})
            
        if User.objects.filter(email__iexact=email).exists():
            return JsonResponse({"success": False, "message": "Account already exists"})

        user = User.objects.create_user(
            username=email, 
            email=email,
            password=signup_data["password"],
            first_name=signup_data["fullname"]
        )
        UserProfile.objects.create(user=user, phone=signup_data["phone"])
        saved.delete()
        request.session.pop("signup_data", None)
        request.session.pop("verify_email", None)
        
        login(request, user)
        return JsonResponse({"success": True, "message": "OTP Verified Successfully"})
        
    except EmailOTP.DoesNotExist:
        return JsonResponse({"success": False, "message": "OTP not found"})
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)})


def login_user(request):
    if request.method == "POST":
        data = json.loads(request.body)
        email_or_user = data.get("email", "").strip()
        password = data.get("password", "").strip()
        
        user = authenticate(request, username=email_or_user, password=password)
        if not user:
            try:
                db_user = User.objects.get(email=email_or_user)
                user = authenticate(request, username=db_user.username, password=password)
            except User.DoesNotExist:
                pass
                
        if user:
            login(request, user)
            return JsonResponse({"success": True, "redirect": "/dashboard/" if user.is_superuser else "/"})
            
        return JsonResponse({"success": False, "message": "Invalid credentials"})
    return JsonResponse({"success": False})


def resend_otp(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid request"})
    try:
        email = request.session.get("verify_email")
        if not email:
            return JsonResponse({"success": False, "message": "Session expired"})
            
        otp = str(random.randint(100000, 999999))
        EmailOTP.objects.filter(
            email=email
        ).delete()

        EmailOTP.objects.create(
            email=email,
            otp=otp
        )
        send_mail(
            subject="SSD Nursery OTP", 
            message=f"Your OTP is {otp}", 
            from_email=None, 
            recipient_list=[email]
        )
        return JsonResponse({"success": True, "message": "OTP resent successfully"})
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)})


def logout_user(request):
    logout(request)
    return redirect("/")


@login_required
def profile(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    orders = Order.objects.filter(user=request.user).order_by("-id")[:10]
    return render(request, "web/profile.html", {"profile": profile, "orders": orders})


@csrf_exempt
def save_details(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid request"})
    try:
        if not request.user.is_authenticated:
            return JsonResponse({"success": False, "message": "Please login first"})
            
        data = json.loads(request.body)
        address = data.get("address", "").strip()
        pincode = data.get("pincode", "").strip()
        instructions = data.get("instructions", "").strip()

        if len(address) < 15:
            return JsonResponse({"success": False, "message": "Address must be at least 15 characters"})
        if not pincode.isdigit() or len(pincode) != 6:
            return JsonResponse({"success": False, "message": "Pincode must be exactly 6 digits"})

        profile, _ = UserProfile.objects.get_or_create(user=request.user)
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
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)})


def reverse_geocode(request):
    lat = request.GET.get("lat")
    lon = request.GET.get("lon")
    try:
        if not lat or not lon:
            return JsonResponse({"success": False, "message": "Lat/Lon required"})
            
        geolocator = Nominatim(user_agent="ssd_nursery")
        location = geolocator.reverse(f"{lat}, {lon}", exactly_one=True, language="en")
        
        if not location:
            return JsonResponse({"success": False, "message": "Location not found"})
            
        addr = location.raw.get("address", {})
        area = addr.get("suburb") or addr.get("neighbourhood") or addr.get("village") or ""
        city = addr.get("city") or addr.get("town") or addr.get("county") or ""
        state = addr.get("state", "")
        pincode = addr.get("postcode") or addr.get("postal_code") or ""
        
        return JsonResponse({
            "success": True, 
            "address": location.address,
            "area": area, 
            "city": city, 
            "state": state, 
            "pincode": pincode
        })
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)})


# ============================================================
# ADMIN DASHBOARD & MANAGEMENT VIEWS
# ============================================================

def _admin_required(func):
    """Decorator: redirect non-superusers to home."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superuser:
            return redirect("/")
        return func(request, *args, **kwargs)
    return wrapper


@login_required
@_admin_required
def admin_dashboard(request):
    total_users = User.objects.count()
    total_cats = Category.objects.count()
    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status="Pending").count()
    completed = Order.objects.filter(status="Delivered").count()
    total_revenue = Order.objects.filter(status="Delivered").aggregate(t=Sum("total_amount"))["t"] or 0
    recent_orders = Order.objects.select_related("user").order_by("-id")[:5]

    return render(request, "web/admin/dashboard.html", {
        "total_users": total_users,
        "total_categories": total_cats,
        "total_products": total_products,
        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "completed_orders": completed,
        "total_revenue": total_revenue,
        "recent_orders": recent_orders,
    })


# --- CATEGORIES ---

@login_required
@_admin_required
def category_list(request):
    categories = Category.objects.all().order_by("-id")
    return render(request, "web/admin/categories.html", {"categories": categories})


@login_required
@_admin_required
def add_category(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "")
        image = request.FILES.get("image")
        
        if Category.objects.filter(name__iexact=name).exists():
            messages.error(request, "Category already exists")
        else:
            Category.objects.create(
                name=name, 
                slug=slugify(name),
                description=description, 
                image=image
            )
            messages.success(request, "Category added successfully")
            
    return redirect("category_list")


@login_required
@_admin_required
def edit_category(request, id):
    category = get_object_or_404(Category, id=id)
    if request.method == "POST":
        category.name = request.POST.get("name", category.name).strip()
        category.description = request.POST.get("description", category.description)
        if request.FILES.get("image"):
            category.image = request.FILES["image"]
        category.save()
        messages.success(request, "Category updated")
    return redirect("category_list")


@login_required
@_admin_required
def toggle_category(request, id):
    category = get_object_or_404(Category, id=id)
    category.is_active = not category.is_active
    category.save()
    return redirect("category_list")


@login_required
@_admin_required
def delete_category(request, id):
    Category.objects.filter(id=id).delete()
    messages.success(request, "Category deleted")
    return redirect("category_list")


# --- PRODUCTS ---

@login_required
@_admin_required
def product_list(request):
    products = Product.objects.select_related("category").all().order_by("-id")
    categories = Category.objects.filter(is_active=True).all()
    return render(request, "web/admin/products.html", {
        "products": products, "categories": categories
    })


@login_required
@_admin_required
def add_product(request):
    if request.method == "POST":
        category = get_object_or_404(Category, id=request.POST.get("category"))
        name = request.POST.get("name", "").strip()
        price = request.POST.get("price")
        offer_price = request.POST.get("offer_price") or None
        stock = request.POST.get("stock", 0)
        description = request.POST.get("description", "")
        care_guide = request.POST.get("care_guide", "")
        image = request.FILES.get("image")
        
        Product.objects.create(
            category=category, name=name, slug=slugify(name),
            price=price, offer_price=offer_price, stock=stock,
            description=description, care_guide=care_guide, image=image
        )
        messages.success(request, f"Product '{name}' added")
    return redirect("product_list")


@login_required
@_admin_required
def edit_product(request, id):
    product = get_object_or_404(Product, id=id)
    if request.method == "POST":
        product.category = get_object_or_404(Category, id=request.POST.get("category"))
        product.name = request.POST.get("name", product.name).strip()
        product.slug = slugify(product.name)
        product.price = request.POST.get("price", product.price)
        product.offer_price = request.POST.get("offer_price") or None
        product.stock = request.POST.get("stock", product.stock)
        product.description = request.POST.get("description", product.description)
        product.care_guide = request.POST.get("care_guide", product.care_guide)
        if request.FILES.get("image"):
            product.image = request.FILES["image"]
        product.save()
        messages.success(request, "Product updated")
    return redirect("product_list")


@login_required
@_admin_required
def toggle_product(request, id):
    product = get_object_or_404(Product, id=id)
    product.is_active = not product.is_active
    product.save()
    return redirect("product_list")


@login_required
@_admin_required
def delete_product(request, id):
    Product.objects.filter(id=id).delete()
    messages.success(request, "Product deleted")
    return redirect("product_list")




@login_required
@_admin_required
def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order.status = request.POST.get("status", order.status)
    order.save()
    return redirect("order_list")


# --- COUPONS ---

@login_required
@_admin_required
def coupon_list(request):
    coupons = Coupon.objects.all().order_by("-id")
    return render(request, "web/admin/coupons.html", {"coupons": coupons})


@login_required
@_admin_required
def add_coupon(request):
    if request.method == "POST":
        Coupon.objects.create(
            code=request.POST.get("code", "").upper(),
            discount_type=request.POST.get("discount_type"),
            discount_value=request.POST.get("discount_value"),
            minimum_order_amount=request.POST.get("minimum_order_amount"),
            maximum_discount=request.POST.get("maximum_discount"),
            expiry_date=request.POST.get("expiry_date")
        )
        messages.success(request, "Coupon created")
    return redirect("coupon_list")


@login_required
@_admin_required
def delete_coupon(request, id):
    Coupon.objects.filter(id=id).delete()
    messages.success(request, "Coupon deleted")
    return redirect("coupon_list")


# --- REVIEWS ---

@login_required
@_admin_required
def reviews_list(request):
    reviews = Review.objects.select_related("user", "product").all().order_by("-id")
    return render(request, "web/admin/reviews.html", {"reviews": reviews})


@login_required
@_admin_required
def approve_review(request, id):
    review = get_object_or_404(Review, id=id)
    review.is_approved = True
    review.save()
    return redirect("reviews_list")


@login_required
@_admin_required
def delete_review(request, id):
    Review.objects.filter(id=id).delete()
    return redirect("reviews_list")


# --- BANNERS ---

@login_required
@_admin_required
def banners_list(request):
    banners = Banner.objects.all().order_by("-id")
    return render(request, "web/admin/banners.html", {"banners": banners})


@login_required
@_admin_required
def add_banner(request):
    if request.method == "POST":
        Banner.objects.create(
            title=request.POST.get("title"),
            banner_type=request.POST.get("banner_type"),
            image=request.FILES.get("image")
        )
        messages.success(request, "Banner added")
    return redirect("banners_list")


@login_required
@_admin_required
def delete_banner(request, id):
    Banner.objects.filter(id=id).delete()
    return redirect("banners_list")


# --- NOTIFICATIONS ---

@login_required
@_admin_required
def notifications_list(request):
    notifications = Notification.objects.all().order_by("-id")
    return render(request, "web/admin/notifications.html", {"notifications": notifications})


@login_required
@_admin_required
def add_notification(request):
    if request.method == "POST":
        Notification.objects.create(
            title=request.POST.get("title"),
            is_active=True
        )
        messages.success(request, "Notification added")
    return redirect("notifications_list")


@login_required
@_admin_required
def delete_notification(request, id):
    Notification.objects.filter(id=id).delete()
    return redirect("notifications_list")


# --- ANALYTICS ---

@login_required
@_admin_required
def analytics(request):
    total_users = User.objects.count()
    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    total_revenue = Order.objects.filter(status="Delivered").aggregate(
        t=Sum("total_amount"))["t"] or 0
        
    # Monthly revenue for chart (last 6 months)
    monthly = (
        Order.objects
        .filter(status="Delivered")
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(revenue=Sum("total_amount"))
        .order_by("month")
    )
    
    chart_labels = [str(m["month"].strftime("%b %Y")) for m in monthly if m["month"]]
    chart_revenue = [float(m["revenue"]) for m in monthly]

    return render(request, "web/admin/analytics.html", {
        "total_users": total_users,
        "total_products": total_products,
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "chart_labels": json.dumps(chart_labels),
        "chart_revenue": json.dumps(chart_revenue),
    })

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
        reviews = Review.objects.all().order_by("-id")[:6]

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

        EmailOTP.objects.filter(
            email=email
        ).delete()

        EmailOTP.objects.create(
            email=email,
            otp=otp
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
            request.session.pop("signup_data", None)
            request.session.pop("verify_email", None)

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
        request.session.pop("signup_data", None)
        request.session.pop("verify_email", None)
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

        EmailOTP.objects.filter(
            email=email
        ).delete()

        EmailOTP.objects.create(
            email=email,
            otp=otp
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
        "profile"
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
    orders = Order.objects.all().order_by('-created_at')

    statuses = [
        'Pending',
        'Confirmed',
        'Packed',
        'Shipped',
        'Delivered',
        'Cancelled'
    ]

    return render(
        request,
        'web/admin/orders.html',
        {
            'orders': orders,
            'statuses': statuses,
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

