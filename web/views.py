from django.db.models.functions import Coalesce
from django.db.models import DecimalField
from django.db.models import Min, Max
import json
import random
import re
import hmac
import hashlib
from datetime import timedelta
from decimal import Decimal

import razorpay
from geopy.geocoders import Nominatim

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Avg, Count, Max, Min, Q, Sum
from django.db.models.functions import TruncMonth
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.text import slugify
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import (
    Banner, CartItem, Category, Coupon,
    EmailOTP, Notification, Order, OrderItem,
    Product, Review, UserProfile, Wishlist,
)


# ══════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════

FREE_DELIVERY_THRESHOLD = Decimal("999")
DELIVERY_CHARGE         = Decimal("49")


# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════

def _admin_required(func):
    """Decorator: block non-superusers."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superuser:
            return redirect("/")
        return func(request, *args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper


def _razorpay_client():
    return razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )


def _delivery_charge(subtotal: Decimal) -> Decimal:
    return Decimal("0") if subtotal >= FREE_DELIVERY_THRESHOLD else DELIVERY_CHARGE


def _unique_slug(model_class, name, exclude_id=None):
    """Generate a unique slug for a model, appending -N on collision."""
    base    = slugify(name)
    slug    = base
    counter = 1
    qs      = model_class.objects.filter(slug=slug)
    if exclude_id:
        qs = qs.exclude(id=exclude_id)
    while qs.exists():
        slug = f"{base}-{counter}"
        counter += 1
        qs = model_class.objects.filter(slug=slug)
        if exclude_id:
            qs = qs.exclude(id=exclude_id)
    return slug


def _resolve_coupon(code: str, subtotal: Decimal):
    """
    Validate coupon.  Returns (coupon_obj, discount) or raises ValueError.
    """
    try:
        coupon = Coupon.objects.get(code=code.upper(), is_active=True)
    except Coupon.DoesNotExist:
        raise ValueError("Invalid or expired coupon.")

    if coupon.expiry_date and coupon.expiry_date < timezone.now().date():
        raise ValueError("Coupon has expired.")

    if subtotal < coupon.minimum_order_amount:
        raise ValueError(f"Minimum order ₹{coupon.minimum_order_amount} required.")

    disc_type = coupon.discount_type.lower()
    if disc_type == "percentage":
        discount = subtotal * coupon.discount_value / 100
        if coupon.maximum_discount:
            discount = min(discount, coupon.maximum_discount)
    else:
        discount = min(coupon.discount_value, subtotal)

    return coupon, discount


def _cart_items(user):
    return CartItem.objects.filter(user=user).select_related("product__category")


def _cart_totals(items):
    """Return (subtotal, item_count)."""
    subtotal = sum(i.product.effective_price * i.quantity for i in items)
    count    = sum(i.quantity for i in items)
    return subtotal, count


def _cart_json_list(items):
    result = []
    for ci in items:
        p = ci.product
        result.append({
            "id":         p.id,
            "name":       p.name,
            "slug":       p.slug,
            "price":      float(p.effective_price),
            "qty":        ci.quantity,
            "subtotal":   float(p.effective_price * ci.quantity),
            "image":      p.image.url if p.image else "",
            "stock":      p.stock,
        })
    return result


def _send_order_confirmation(order):
    """Send order confirmation email — silently swallow SMTP errors."""
    try:
        items_text = "\n".join(
            f"  • {i.product.name}  x{i.quantity}  ₹{i.price * i.quantity}"
            for i in order.items.select_related("product")
        )
        send_mail(
            subject=f"SSD Nursery — Order #{order.id} Confirmed 🌱",
            message=(
                f"Hi {order.user.first_name or order.user.username},\n\n"
                f"Your order has been placed successfully!\n\n"
                f"Order ID : #{order.id}\n"
                f"Amount   : ₹{order.total_amount}\n"
                f"Payment  : {order.payment_method.upper()}\n"
                f"Status   : {order.status}\n\n"
                f"Items:\n{items_text}\n\n"
                f"Delivery to:\n{order.address}\n\n"
                f"Thank you for shopping with SSD Nursery!\n— Team SSD Nursery"
            ),
            from_email=None,
            recipient_list=[order.user.email],
        )
    except Exception:
        pass   # never crash on email failure


# ══════════════════════════════════════════════════════════════
# HOME
# ══════════════════════════════════════════════════════════════

def home(request):
    banners       = Banner.objects.filter(is_active=True).order_by("sort_order", "-created_at")[:5]
    categories    = Category.objects.filter(is_active=True).order_by("name")
    products      = Product.objects.filter(is_active=True).select_related("category").order_by("-id")[:8]
    reviews       = Review.objects.filter(is_approved=True).select_related("user").order_by("-id")[:6]
    notifications = Notification.objects.filter(is_active=True).order_by("-id")[:5]

    wishlist_ids = []
    if request.user.is_authenticated:
        wishlist_ids = list(
            Wishlist.objects.filter(user=request.user).values_list("product_id", flat=True)
        )

    return render(request, "web/home.html", {
        "banners":       banners,
        "categories":    categories,
        "products":      products,
        "reviews":       reviews,
        "notifications": notifications,
        "wishlist_ids":  wishlist_ids,
    })


# ══════════════════════════════════════════════════════════════
# COLLECTIONS
# ══════════════════════════════════════════════════════════════

def collections(request):
    categories = Category.objects.filter(is_active=True).annotate(
        product_count=Count("products", filter=Q(products__is_active=True))
    ).order_by("name")
    return render(request, "web/collections.html", {"categories": categories})


# ══════════════════════════════════════════════════════════════
# SHOP
# ══════════════════════════════════════════════════════════════

def shop(request):
    bounds = (
        Product.objects.filter(is_active=True)
        .annotate(
            final_price=Coalesce(
                "offer_price",
                "price",
                output_field=DecimalField()
            )
        )
        .aggregate(
            mn=Min("final_price"),
            mx=Max("final_price")
        )
    )

    global_min = int(bounds["mn"] or 0)
    global_max = int(bounds["mx"] or 0)

    qs = (
        Product.objects.filter(is_active=True)
        .select_related("category")
        .annotate(
            final_price=Coalesce(
                "offer_price",
                "price",
                output_field=DecimalField()
            )
        )
    )
    # Category
    cat_slug        = request.GET.get("category", "").strip()
    active_category = None
    if cat_slug:
        active_category = get_object_or_404(Category, slug=cat_slug, is_active=True)
        qs = qs.filter(category=active_category)

    # Search
    query = request.GET.get("q", "").strip()
    if query:
        qs = qs.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        )

    # Price bounds
    min_price = request.GET.get("min_price", "")
    max_price = request.GET.get("max_price", "")
    if min_price.lstrip("-").isdigit():
        qs = qs.filter(final_price__gte=int(min_price))
    if max_price.lstrip("-").isdigit():
        qs = qs.filter(final_price__lte=int(max_price))

    if request.GET.get("sale") == "1":
        qs = qs.exclude(offer_price__isnull=True)
    if request.GET.get("in_stock") == "1":
        qs = qs.filter(stock__gt=0)

    sort     = request.GET.get("sort", "newest")
    sort_map = {"newest": "-id", "price_asc": "final_price", "price_desc": "-final_price", "name_asc": "name"}
    qs       = qs.order_by(sort_map.get(sort, "-id"))

    paginator = Paginator(qs, 12)
    page_obj  = paginator.get_page(request.GET.get("page", 1))
    categories = Category.objects.filter(is_active=True).order_by("name")

    qp = request.GET.copy()
    qp.pop("page", None)

    wishlist_ids = []
    if request.user.is_authenticated:
        wishlist_ids = list(
            Wishlist.objects.filter(user=request.user).values_list("product_id", flat=True)
        )

    return render(request, "web/shop.html", {
        "page_obj":        page_obj,
        "categories":      categories,
        "active_category": active_category,
        "query":           query,
        "sort":            sort,
        "min_price":       min_price or global_min,
        "max_price":       max_price or global_max,
        "global_min":      global_min,
        "global_max":      global_max,
        "sale_only":       request.GET.get("sale", ""),
        "stock_only":      request.GET.get("in_stock", ""),
        "filter_string":   qp.urlencode(),
        "total_count":     paginator.count,
        "wishlist_ids":    wishlist_ids,
    })


# ══════════════════════════════════════════════════════════════
# SEARCH SUGGESTIONS (AJAX)
# ══════════════════════════════════════════════════════════════

def search_suggestions(request):
    q = request.GET.get("q", "").strip()

    if len(q) < 2:
        return JsonResponse({"groups": []})

    categories = Category.objects.filter(
        is_active=True,
        name__icontains=q
    )[:6]

    groups = []

    for category in categories:

        products = Product.objects.filter(
            is_active=True,
            category=category
        )[:4]

        groups.append({
            "category": {
                "id": category.id,
                "name": category.name,
                "slug": category.slug,
                "image": category.image.url if category.image else "",
            },
            "products": [
                {
                    "id": p.id,
                    "name": p.name,
                    "slug": p.slug,
                    "price": str(p.offer_price or p.price),
                    "image": p.image.url if p.image else "",
                }
                for p in products
            ]
        })

    if not groups:

        products = Product.objects.filter(
            is_active=True,
            name__icontains=q
        ).select_related("category")[:8]

        grouped = {}

        for p in products:

            cat = p.category

            if cat.id not in grouped:
                grouped[cat.id] = {
                    "category": {
                        "id": cat.id,
                        "name": cat.name,
                        "slug": cat.slug,
                        "image": cat.image.url if cat.image else "",
                    },
                    "products": []
                }

            grouped[cat.id]["products"].append({
                "id": p.id,
                "name": p.name,
                "slug": p.slug,
                "price": str(p.offer_price or p.price),
                "image": p.image.url if p.image else "",
            })

        groups = list(grouped.values())

    return JsonResponse({
        "groups": groups
    })


# ══════════════════════════════════════════════════════════════
# PRODUCT DETAIL & REVIEW
# ══════════════════════════════════════════════════════════════

def product_detail(request, slug):
    product    = get_object_or_404(Product, slug=slug, is_active=True)

    reviews    = Review.objects.filter(product=product).select_related("user")

    related    = Product.objects.filter(
        category=product.category,
        is_active=True
    ).exclude(id=product.id).order_by("-id")[:4]

    avg_rating = reviews.aggregate(avg=Avg("rating"))["avg"] or 0

    user_review  = None
    in_wishlist  = False
    cart_qty     = 0
    has_purchased = False
    if request.user.is_authenticated:

        user_review = Review.objects.filter(
            product=product,
            user=request.user
        ).first()

        has_purchased = OrderItem.objects.filter(
            order__user=request.user,
            order__status="Delivered",
            product=product
        ).exists()

        in_wishlist = Wishlist.objects.filter(
            user=request.user,
            product=product
        ).exists()

        ci = CartItem.objects.filter(
            user=request.user,
            product=product
        ).first()

        cart_qty = ci.quantity if ci else 0

    return render(request, "web/product_detail.html", {
        "product":     product,
        "reviews":     reviews,
        "related":     related,
        "avg_rating":  round(avg_rating, 1),
        "user_review": user_review,
        "in_wishlist": in_wishlist,
        "cart_qty":    cart_qty,
    })


@login_required
def submit_review(request, product_id):
    if request.method != "POST":
        return JsonResponse({
            "success": False,
            "message": "Invalid request"
        })

    try:
        product = get_object_or_404(Product, id=product_id)

        # Check purchase history
        has_purchased = OrderItem.objects.filter(
            order__user=request.user,
            order__status="Delivered",
            product=product
        ).exists()

        if not has_purchased:
            return JsonResponse({
                "success": False,
                "message": "You can review only products you have purchased."
            })

        # Check existing review
        if Review.objects.filter(
            product=product,
            user=request.user
        ).exists():
            return JsonResponse({
                "success": False,
                "message": "You have already reviewed this product."
            })

        data = json.loads(request.body)

        rating = max(
            1,
            min(5, int(data.get("rating", 5)))
        )

        review_text = data.get("review", "").strip()

        if len(review_text) < 10:
            return JsonResponse({
                "success": False,
                "message": "Review must contain at least 10 characters."
            })

        Review.objects.create(
            product=product,
            user=request.user,
            rating=rating,
            review=review_text
        )

        return JsonResponse({
            "success": True,
            "message": "Thank you for your review!"
        })

    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": str(e)
        })

# ══════════════════════════════════════════════════════════════
# AUTHENTICATION
# ══════════════════════════════════════════════════════════════

def auth_page(request):
    return render(request, "web/auth.html")


def send_signup_otp(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid request"})
    try:
        data     = json.loads(request.body)
        fullname = data.get("fullname", "").strip()
        email    = data.get("email", "").strip().lower()
        phone    = data.get("phone", "").strip()
        password = data.get("password", "")

        # Validate
        if len(fullname) < 3:
            return JsonResponse({"success": False, "message": "Name must be at least 3 characters."})
        if not re.match(r"^[A-Za-z ]+$", fullname):
            return JsonResponse({"success": False, "message": "Name should contain only letters."})
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            return JsonResponse({"success": False, "message": "Enter a valid email address."})
        if User.objects.filter(email__iexact=email).exists():
            return JsonResponse({"success": False, "message": "Email already registered."})
        if not phone.isdigit() or len(phone) != 10:
            return JsonResponse({"success": False, "message": "Phone must be exactly 10 digits."})
        if UserProfile.objects.filter(phone=phone).exists():
            return JsonResponse({"success": False, "message": "Phone already registered."})
        if (len(password) < 8
                or not re.search(r"[A-Z]", password)
                or not re.search(r"[a-z]", password)
                or not re.search(r"\d", password)
                or not re.search(r"[!@#$%^&*()_+=\-{}[\]:;'<>,.?/]", password)):
            return JsonResponse({"success": False,
                "message": "Password needs 8+ chars, uppercase, lowercase, digit and special character."})

        otp = str(random.randint(100000, 999999))
        EmailOTP.objects.update_or_create(email=email, defaults={"otp": otp})
        request.session["signup_data"]  = {
            "fullname": fullname, "email": email,
            "phone":    phone,    "password": password,
        }
        request.session["verify_email"] = email

        # Wrap mail so a bad SMTP config never kills signup flow
        try:
            send_mail(
                subject="SSD Nursery — Verify Your Email",
                message=(
                    f"Hi {fullname},\n\n"
                    f"Your OTP is: {otp}\n\n"
                    f"Valid for 5 minutes.\n\n— SSD Nursery"
                ),
                from_email=None,
                recipient_list=[email],
            )
        except Exception:
            return JsonResponse({"success": False, "message": "Unable to send OTP email. Please try again."})

        return JsonResponse({"success": True, "message": "OTP sent successfully!"})

    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)})


def verify_signup_otp(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid request"})
    try:
        data  = json.loads(request.body)
        email = request.session.get("verify_email")
        otp   = data.get("otp")
        saved = EmailOTP.objects.get(email=email)

        if timezone.now() - saved.created_at > timedelta(minutes=5):
            saved.delete()
            request.session.pop("signup_data", None)
            request.session.pop("verify_email", None)
            return JsonResponse({"success": False, "message": "OTP expired. Request a new one."})

        if saved.otp != otp:
            return JsonResponse({"success": False, "message": "Invalid OTP."})

        signup_data = request.session.get("signup_data")
        if not signup_data:
            return JsonResponse({"success": False, "message": "Session expired. Please sign up again."})
        if User.objects.filter(email__iexact=email).exists():
            return JsonResponse({"success": False, "message": "Account already exists."})

        user = User.objects.create_user(
            username=email, email=email,
            password=signup_data["password"],
            first_name=signup_data["fullname"],
        )
        UserProfile.objects.create(user=user, phone=signup_data["phone"])
        saved.delete()

        # Fix Issue 13: clean session after verified
        request.session.pop("signup_data", None)
        request.session.pop("verify_email", None)

        login(request, user)
        return JsonResponse({"success": True, "message": "OTP verified!"})

    except EmailOTP.DoesNotExist:
        return JsonResponse({"success": False, "message": "OTP not found."})
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)})


def resend_otp(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid request"})
    try:
        email = request.session.get("verify_email")
        if not email:
            return JsonResponse({"success": False, "message": "Session expired."})
        otp = str(random.randint(100000, 999999))
        EmailOTP.objects.update_or_create(email=email, defaults={"otp": otp})
        try:
            send_mail(
                subject="SSD Nursery OTP",
                message=f"Your new OTP is: {otp}",
                from_email=None,
                recipient_list=[email],
            )
        except Exception:
            return JsonResponse({"success": False, "message": "Could not send OTP email."})
        return JsonResponse({"success": True, "message": "OTP resent!"})
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)})


def login_user(request):
    if request.method != "POST":
        return JsonResponse({"success": False})
    data          = json.loads(request.body)
    email_or_user = data.get("email", "").strip()
    password      = data.get("password", "").strip()

    user = authenticate(request, username=email_or_user, password=password)
    if not user:
        try:
            db_user = User.objects.get(email=email_or_user)
            user    = authenticate(request, username=db_user.username, password=password)
        except User.DoesNotExist:
            pass

    if user:
        login(request, user)
        return JsonResponse({"success": True, "redirect": "/dashboard/" if user.is_superuser else "/"})
    return JsonResponse({"success": False, "message": "Invalid credentials."})


def logout_user(request):
    logout(request)
    return redirect("/")


# ══════════════════════════════════════════════════════════════
# USER PROFILE
# ══════════════════════════════════════════════════════════════

@login_required
def profile(request):
    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
    orders   = Order.objects.filter(user=request.user).prefetch_related("items__product").order_by("-id")[:10]
    wishlist = Wishlist.objects.filter(user=request.user).select_related("product").order_by("-added_at")[:6]
    return render(request, "web/profile.html", {
        "profile":  user_profile,
        "orders":   orders,
        "wishlist": wishlist,
    })


@csrf_exempt
@login_required
def save_details(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid request"})
    try:
        data         = json.loads(request.body)
        address      = data.get("address", "").strip()
        pincode      = data.get("pincode", "").strip()
        if len(address) < 10:
            return JsonResponse({"success": False, "message": "Address must be at least 10 characters."})
        if not pincode.isdigit() or len(pincode) != 6:
            return JsonResponse({"success": False, "message": "Pincode must be 6 digits."})
        profile, _          = UserProfile.objects.get_or_create(user=request.user)
        profile.address      = address
        profile.area         = data.get("area", "")
        profile.city         = data.get("city", "")
        profile.state        = data.get("state", "")
        profile.pincode      = pincode
        profile.instructions = data.get("instructions", "")
        profile.save()
        return JsonResponse({"success": True, "message": "Details saved!"})
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)})


def reverse_geocode(request):
    lat = request.GET.get("lat")
    lon = request.GET.get("lon")
    try:
        if not lat or not lon:
            return JsonResponse({"success": False, "message": "Lat/Lon required."})
        # Fix Issue 9: geopy timeout
        geo      = Nominatim(user_agent="ssd_nursery", timeout=10)
        location = geo.reverse(f"{lat}, {lon}", exactly_one=True, language="en")
        if not location:
            return JsonResponse({"success": False, "message": "Location not found."})
        addr = location.raw.get("address", {})
        return JsonResponse({
            "success": True,
            "address": location.address,
            "area":    addr.get("suburb") or addr.get("neighbourhood") or addr.get("village") or "",
            "city":    addr.get("city") or addr.get("town") or addr.get("county") or "",
            "state":   addr.get("state", ""),
            "pincode": addr.get("postcode") or "",
        })
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)})


# ══════════════════════════════════════════════════════════════
# CART
# ══════════════════════════════════════════════════════════════

def cart_page(request):
    if not request.user.is_authenticated:
        return redirect("/auth/?tab=login&next=/cart/")
    items    = _cart_items(request.user)
    subtotal, count = _cart_totals(items)
    delivery = _delivery_charge(subtotal)
    return render(request, "web/cart.html", {
        "items":    items,
        "subtotal": subtotal,
        "delivery": delivery,
        "total":    subtotal + delivery,
        "count":    count,
    })


@require_POST
def cart_add(request):
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "message": "login_required"})
    try:
        data    = json.loads(request.body)
        product = get_object_or_404(Product, id=data["product_id"], is_active=True)
        qty     = max(1, int(data.get("qty", 1)))
        if product.stock == 0:
            return JsonResponse({"success": False, "message": "Out of stock"})
        ci, _       = CartItem.objects.get_or_create(user=request.user, product=product, defaults={"quantity": 0})
        ci.quantity = min(ci.quantity + qty, product.stock)
        ci.save()
        items = _cart_items(request.user)
        _, count = _cart_totals(items)
        subtotal, count = _cart_totals(items)

        return JsonResponse({
            "success": True,
            "message": f"{product.name} added to cart!",
            "cart": _cart_json_list(items),
            "subtotal": float(subtotal),
            "count": count,
        })
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)})


@require_POST
def cart_update(request):
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "message": "login_required"})
    try:
        data = json.loads(request.body)
        ci   = get_object_or_404(CartItem, user=request.user, product_id=data["product_id"])
        qty  = int(data.get("qty", 1))
        if qty <= 0:
            ci.delete()
        else:
            ci.quantity = min(qty, ci.product.stock)
            ci.save()
        items = _cart_items(request.user)
        subtotal, count = _cart_totals(items)
        return JsonResponse({
            "success":  True,
            "cart":     _cart_json_list(items),
            "subtotal": float(subtotal),
            "count":    count,
        })
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)})


@require_POST
def cart_remove(request):
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "message": "login_required"})
    try:
        data = json.loads(request.body)
        CartItem.objects.filter(user=request.user, product_id=data["product_id"]).delete()
        items = _cart_items(request.user)
        subtotal, count = _cart_totals(items)
        return JsonResponse({
            "success":  True,
            "cart":     _cart_json_list(items),
            "subtotal": float(subtotal),
            "count":    count,
        })
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)})


def cart_data(request):
    if not request.user.is_authenticated:
        return JsonResponse({"cart": [], "subtotal": 0, "count": 0})
    items = _cart_items(request.user)
    subtotal, count = _cart_totals(items)
    return JsonResponse({
        "cart":     _cart_json_list(items),
        "subtotal": float(subtotal),
        "count":    count,
    })


@require_POST
def cart_clear(request):
    if request.user.is_authenticated:
        CartItem.objects.filter(user=request.user).delete()
    return JsonResponse({"success": True})


# ══════════════════════════════════════════════════════════════
# WISHLIST
# ══════════════════════════════════════════════════════════════

def wishlist_page(request):
    if not request.user.is_authenticated:
        return redirect("/auth/?tab=login&next=/wishlist/")
    items = Wishlist.objects.filter(user=request.user).select_related("product__category").order_by("-added_at")
    return render(request, "web/wishlist.html", {"items": items})


@require_POST
def wishlist_toggle(request):
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "message": "login_required"})
    try:
        data    = json.loads(request.body)
        product = get_object_or_404(Product, id=data["product_id"], is_active=True)
        obj, created = Wishlist.objects.get_or_create(user=request.user, product=product)
        if not created:
            obj.delete()
            return JsonResponse({"success": True, "action": "removed",
                                 "message": f"{product.name} removed from wishlist"})
        return JsonResponse({"success": True, "action": "added",
                             "message": f"{product.name} added to wishlist!"})
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)})


def wishlist_data(request):
    if not request.user.is_authenticated:
        return JsonResponse({"ids": []})
    ids = list(Wishlist.objects.filter(user=request.user).values_list("product_id", flat=True))
    return JsonResponse({"ids": ids})


# ══════════════════════════════════════════════════════════════
# COUPON (AJAX)
# ══════════════════════════════════════════════════════════════

@require_POST
def apply_coupon(request):
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "message": "login_required"})
    try:
        data     = json.loads(request.body)
        code     = data.get("code", "").strip()
        subtotal = Decimal(str(data.get("subtotal", "0")))
        coupon, discount = _resolve_coupon(code, subtotal)
        return JsonResponse({
            "success":  True,
            "message":  f"Coupon applied! You save ₹{discount:.0f}",
            "discount": float(discount),
            "total":    float(subtotal - discount),
        })
    except ValueError as e:
        return JsonResponse({"success": False, "message": str(e)})
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)})


# ══════════════════════════════════════════════════════════════
# CHECKOUT PAGE
# ══════════════════════════════════════════════════════════════

@login_required
def checkout(request):
    items = _cart_items(request.user)
    if not items.exists():
        return redirect("cart_page")
    subtotal, _ = _cart_totals(items)
    delivery    = _delivery_charge(subtotal)
    total       = subtotal + delivery
    profile, _  = UserProfile.objects.get_or_create(user=request.user)
    return render(request, "web/checkout.html", {
        "items":        items,
        "subtotal":     subtotal,
        "delivery":     delivery,
        "total":        total,
        "profile":      profile,
        "razorpay_key": settings.RAZORPAY_KEY_ID,
    })


# ══════════════════════════════════════════════════════════════
# RAZORPAY — create order (AJAX)
# ══════════════════════════════════════════════════════════════

@require_POST
@login_required
def create_razorpay_order(request):
    try:
        data  = json.loads(request.body)
        items = _cart_items(request.user)
        if not items.exists():
            return JsonResponse({"success": False, "message": "Cart is empty."})

        subtotal, _ = _cart_totals(items)
        delivery    = _delivery_charge(subtotal)

        # Fix Issue 6: stock validation before payment
        for ci in items:
            if ci.quantity > ci.product.stock:
                return JsonResponse({
                    "success": False,
                    "message": f"'{ci.product.name}' has only {ci.product.stock} left in stock.",
                })

        discount   = Decimal("0")
        coupon_obj = None
        code       = data.get("coupon_code", "").strip()
        if code:
            try:
                coupon_obj, discount = _resolve_coupon(code, subtotal)
            except ValueError as e:
                return JsonResponse({"success": False, "message": str(e)})

        total        = subtotal + delivery - discount
        amount_paise = int(total * 100)

        client   = _razorpay_client()
        rz_order = client.order.create({
            "amount":   amount_paise,
            "currency": "INR",
            "receipt":  f"ssd_{request.user.id}_{int(timezone.now().timestamp())}",
        })

        # Fix Issue 2: store as string not float
        request.session["pending_checkout"] = {
            "subtotal":    str(subtotal),
            "delivery":    str(delivery),
            "discount":    str(discount),
            "total":       str(total),
            "coupon_id":   coupon_obj.id if coupon_obj else None,
            "rz_order_id": rz_order["id"],
            "address":     data.get("address", ""),
            "notes":       data.get("notes", ""),
        }

        return JsonResponse({
            "success":  True,
            "order_id": rz_order["id"],
            "amount":   amount_paise,
            "currency": "INR",
            "key":      settings.RAZORPAY_KEY_ID,
            "name":     request.user.first_name or request.user.username,
            "email":    request.user.email,
        })
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)})


# ══════════════════════════════════════════════════════════════
# RAZORPAY — verify payment + place order (AJAX)
# ══════════════════════════════════════════════════════════════

@require_POST
@login_required
@csrf_exempt
def verify_razorpay_payment(request):
    try:
        data    = json.loads(request.body)
        pending = request.session.get("pending_checkout")
        if not pending:
            return JsonResponse({"success": False, "message": "Session expired. Please retry checkout."})

        rz_order_id   = data.get("razorpay_order_id", "")
        rz_payment_id = data.get("razorpay_payment_id", "")
        rz_signature  = data.get("razorpay_signature", "")

        # Fix Issue 4: official Razorpay signature verification
        client = _razorpay_client()
        try:
            client.utility.verify_payment_signature({
                "razorpay_order_id":   rz_order_id,
                "razorpay_payment_id": rz_payment_id,
                "razorpay_signature":  rz_signature,
            })
        except razorpay.errors.SignatureVerificationError:
            return JsonResponse({"success": False, "message": "Payment verification failed."})

        # Fix Issue 3: idempotency — block duplicate order for same payment
        if Order.objects.filter(payment_id=rz_payment_id).exists():
            existing = Order.objects.get(payment_id=rz_payment_id)
            return JsonResponse({"success": True, "order_id": existing.id})

        items = _cart_items(request.user)
        if not items.exists():
            return JsonResponse({"success": False, "message": "Cart is empty."})

        # Fix Issue 2: Decimal from session strings
        total    = Decimal(pending["total"])
        discount = Decimal(pending["discount"])
        coupon   = Coupon.objects.filter(id=pending["coupon_id"]).first() if pending["coupon_id"] else None

        # Fix Issue 5: transaction.atomic + SELECT FOR UPDATE
        with transaction.atomic():
            order = Order.objects.create(
                user            = request.user,
                total_amount    = total,
                discount_amount = discount,
                status          = "Confirmed",
                payment_method  = "razorpay",
                payment_id      = rz_payment_id,
                razorpay_order_id = rz_order_id,
                address         = pending["address"],
                notes           = pending["notes"],
                coupon          = coupon,
            )
            for ci in items.select_for_update():
                # Fix Issue 6: final stock re-check inside transaction
                if ci.quantity > ci.product.stock:
                    raise ValueError(f"'{ci.product.name}' ran out of stock.")
                OrderItem.objects.create(
                    order    = order,
                    product  = ci.product,
                    quantity = ci.quantity,
                    price    = ci.product.effective_price,
                )
                ci.product.stock = max(0, ci.product.stock - ci.quantity)
                ci.product.save(update_fields=["stock"])

            items.delete()

        if "pending_checkout" in request.session:
            del request.session["pending_checkout"]

        # Fix Issue 14: confirmation email
        _send_order_confirmation(order)

        return JsonResponse({"success": True, "order_id": order.id})

    except ValueError as e:
        return JsonResponse({"success": False, "message": str(e)})
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)})


# ══════════════════════════════════════════════════════════════
# COD ORDER
# ══════════════════════════════════════════════════════════════

@require_POST
@login_required
def place_cod_order(request):
    try:
        data  = json.loads(request.body)
        items = _cart_items(request.user)
        if not items.exists():
            return JsonResponse({"success": False, "message": "Cart is empty."})

        subtotal, _ = _cart_totals(items)
        delivery    = _delivery_charge(subtotal)

        # Stock validation
        for ci in items:
            if ci.quantity > ci.product.stock:
                return JsonResponse({
                    "success": False,
                    "message": f"'{ci.product.name}' has only {ci.product.stock} left.",
                })

        discount   = Decimal("0")
        coupon_obj = None
        code       = data.get("coupon_code", "").strip()
        if code:
            try:
                coupon_obj, discount = _resolve_coupon(code, subtotal)
            except ValueError as e:
                return JsonResponse({"success": False, "message": str(e)})

        total = subtotal + delivery - discount

        with transaction.atomic():
            order = Order.objects.create(
                user            = request.user,
                total_amount    = total,
                discount_amount = discount,
                status          = "Pending",
                payment_method  = "cod",
                address         = data.get("address", ""),
                notes           = data.get("notes", ""),
                coupon          = coupon_obj,
            )
            for ci in items.select_for_update():
                if ci.quantity > ci.product.stock:
                    raise ValueError(f"'{ci.product.name}' ran out of stock.")
                OrderItem.objects.create(
                    order=order, product=ci.product,
                    quantity=ci.quantity, price=ci.product.effective_price,
                )
                ci.product.stock = max(0, ci.product.stock - ci.quantity)
                ci.product.save(update_fields=["stock"])

            items.delete()

        _send_order_confirmation(order)
        return JsonResponse({"success": True, "order_id": order.id})

    except ValueError as e:
        return JsonResponse({"success": False, "message": str(e)})
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)})


# ══════════════════════════════════════════════════════════════
# ORDER SUCCESS
# ══════════════════════════════════════════════════════════════

@login_required
def order_success(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related("items__product"),
        id=order_id, user=request.user,
    )
    return render(request, "web/order_success.html", {"order": order, "items": order.items.all()})


# ══════════════════════════════════════════════════════════════
# ADMIN — DASHBOARD
# ══════════════════════════════════════════════════════════════

@login_required
@_admin_required
def admin_dashboard(request):
    total_revenue = Order.objects.filter(status="Delivered").aggregate(t=Sum("total_amount"))["t"] or 0
    return render(request, "web/admin/dashboard.html", {
        "total_users":      User.objects.count(),
        "total_categories": Category.objects.count(),
        "total_products":   Product.objects.count(),
        "total_orders":     Order.objects.count(),
        "pending_orders":   Order.objects.filter(status="Pending").count(),
        "completed_orders": Order.objects.filter(status="Delivered").count(),
        "total_revenue":    total_revenue,
        "recent_orders":    Order.objects.select_related("user").order_by("-id")[:5],
    })


@login_required
@_admin_required
def users_list(request):
    users = User.objects.select_related("profile").order_by("-date_joined")
    return render(request, "web/admin/users.html", {"users": users})


# ── Categories ────────────────────────────────────────────────

@login_required
@_admin_required
def category_list(request):
    return render(request, "web/admin/categories.html",
                  {"categories": Category.objects.all().order_by("-id")})


@login_required
@_admin_required
def add_category(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        if Category.objects.filter(name__iexact=name).exists():
            messages.error(request, "Category already exists.")
        else:
            Category.objects.create(
                name=name, slug=slugify(name),
                description=request.POST.get("description", ""),
                image=request.FILES.get("image"),
            )
            messages.success(request, f"Category '{name}' added.")
    return redirect("category_list")


@login_required
@_admin_required
def edit_category(request, id):
    cat = get_object_or_404(Category, id=id)
    if request.method == "POST":
        cat.name        = request.POST.get("name", cat.name).strip()
        cat.slug        = slugify(cat.name)
        cat.description = request.POST.get("description", cat.description)
        if request.FILES.get("image"):
            cat.image = request.FILES["image"]
        cat.save()
        messages.success(request, "Category updated.")
    return redirect("category_list")


@login_required
@_admin_required
def toggle_category(request, id):
    cat           = get_object_or_404(Category, id=id)
    cat.is_active = not cat.is_active
    cat.save()
    return redirect("category_list")


@login_required
@_admin_required
def delete_category(request, id):
    Category.objects.filter(id=id).delete()
    messages.success(request, "Category deleted.")
    return redirect("category_list")


# ── Products ──────────────────────────────────────────────────

@login_required
@_admin_required
def product_list(request):
    return render(request, "web/admin/products.html", {
        "products":   Product.objects.select_related("category").order_by("-id"),
        "categories": Category.objects.filter(is_active=True),
    })


@login_required
@_admin_required
def add_product(request):
    if request.method == "POST":
        cat  = get_object_or_404(Category, id=request.POST.get("category"))
        name = request.POST.get("name", "").strip()
        # Fix Issue 7: unique slug
        slug = _unique_slug(Product, name)
        Product.objects.create(
            category=cat, name=name, slug=slug,
            price=request.POST.get("price"),
            offer_price=request.POST.get("offer_price") or None,
            stock=request.POST.get("stock", 0),
            description=request.POST.get("description", ""),
            care_guide=request.POST.get("care_guide", ""),
            image=request.FILES.get("image"),
        )
        messages.success(request, f"Product '{name}' added.")
    return redirect("product_list")


@login_required
@_admin_required
def edit_product(request, id):
    p = get_object_or_404(Product, id=id)
    if request.method == "POST":
        p.category    = get_object_or_404(Category, id=request.POST.get("category"))
        p.name        = request.POST.get("name", p.name).strip()
        p.slug        = _unique_slug(Product, p.name, exclude_id=p.id)   # Fix Issue 7
        p.price       = request.POST.get("price", p.price)
        p.offer_price = request.POST.get("offer_price") or None
        p.stock       = request.POST.get("stock", p.stock)
        p.description = request.POST.get("description", p.description)
        p.care_guide  = request.POST.get("care_guide", p.care_guide)
        if request.FILES.get("image"):
            p.image = request.FILES["image"]
        p.save()
        messages.success(request, "Product updated.")
    return redirect("product_list")


@login_required
@_admin_required
def toggle_product(request, id):
    p           = get_object_or_404(Product, id=id)
    p.is_active = not p.is_active
    p.save()
    return redirect("product_list")


@login_required
@_admin_required
def delete_product(request, id):
    Product.objects.filter(id=id).delete()
    messages.success(request, "Product deleted.")
    return redirect("product_list")


# ── Orders ────────────────────────────────────────────────────

@login_required
@_admin_required
def order_list(request):
    orders   = Order.objects.select_related("user").order_by("-id")
    statuses = ["Pending", "Confirmed", "Packed", "Shipped", "Delivered", "Cancelled"]
    return render(request, "web/admin/orders.html", {"orders": orders, "statuses": statuses})


@login_required
@_admin_required
def update_order_status(request, order_id):
    order        = get_object_or_404(Order, id=order_id)
    order.status = request.POST.get("status", order.status)
    order.save()
    return redirect("order_list")


# ── Coupons ───────────────────────────────────────────────────

@login_required
@_admin_required
def coupon_list(request):
    return render(request, "web/admin/coupons.html",
                  {"coupons": Coupon.objects.order_by("-id")})


@login_required
@_admin_required
def add_coupon(request):
    if request.method == "POST":
        Coupon.objects.create(
            code=request.POST.get("code", "").upper(),
            discount_type=request.POST.get("discount_type"),
            discount_value=request.POST.get("discount_value"),
            minimum_order_amount=request.POST.get("minimum_order_amount") or 0,
            maximum_discount=request.POST.get("maximum_discount") or None,
            expiry_date=request.POST.get("expiry_date") or None,
        )
        messages.success(request, "Coupon created.")
    return redirect("coupon_list")


@login_required
@_admin_required
def delete_coupon(request, id):
    Coupon.objects.filter(id=id).delete()
    return redirect("coupon_list")


# ── Reviews ───────────────────────────────────────────────────

@login_required
@_admin_required
def reviews_list(request):
    return render(request, "web/admin/reviews.html", {
        "reviews": Review.objects.select_related("user", "product").order_by("-id"),
    })




@login_required
@_admin_required
def delete_review(request, id):
    Review.objects.filter(id=id).delete()
    return redirect("reviews_list")


# ── Banners ───────────────────────────────────────────────────

@login_required
@_admin_required
def banners_list(request):
    return render(request, "web/admin/banners.html", {
        "banners": Banner.objects.order_by("sort_order", "-created_at"),
    })


@login_required
@_admin_required
def add_banner(request):
    if request.method == "POST":
        Banner.objects.create(
            image        = request.FILES.get("image"),
            tag_text     = request.POST.get("tag_text", ""),
            heading      = request.POST.get("heading", ""),
            subheading   = request.POST.get("subheading", ""),
            description  = request.POST.get("description", ""),
            button_text  = request.POST.get("button_text", ""),
            button_url   = request.POST.get("button_url", ""),
            button_style = request.POST.get("button_style", "primary"),
            banner_type  = request.POST.get("banner_type", "hero"),
            sort_order   = request.POST.get("sort_order", 0) or 0,
        )
        messages.success(request, "Banner added.")
    return redirect("banners_list")


@login_required
@_admin_required
def edit_banner(request, id):
    b = get_object_or_404(Banner, id=id)
    if request.method == "POST":
        b.tag_text    = request.POST.get("tag_text",    b.tag_text)
        b.heading     = request.POST.get("heading",     b.heading)
        b.subheading  = request.POST.get("subheading",  b.subheading)
        b.description = request.POST.get("description", b.description)
        b.button_text = request.POST.get("button_text", b.button_text)
        b.button_url  = request.POST.get("button_url",  b.button_url)
        b.button_style= request.POST.get("button_style",b.button_style)
        b.banner_type = request.POST.get("banner_type", b.banner_type)
        b.sort_order  = request.POST.get("sort_order",  b.sort_order) or 0
        if request.FILES.get("image"):
            b.image = request.FILES["image"]
        b.save()
        messages.success(request, "Banner updated.")
    return redirect("banners_list")


@login_required
@_admin_required
def toggle_banner(request, id):
    b           = get_object_or_404(Banner, id=id)
    b.is_active = not b.is_active
    b.save()
    return redirect("banners_list")


@login_required
@_admin_required
def delete_banner(request, id):
    Banner.objects.filter(id=id).delete()
    return redirect("banners_list")


# ── Notifications ─────────────────────────────────────────────

@login_required
@_admin_required
def notifications_list(request):
    return render(request, "web/admin/notifications.html", {
        "notifications": Notification.objects.order_by("-id"),
    })


@login_required
@_admin_required
def add_notification(request):
    if request.method == "POST":
        Notification.objects.create(title=request.POST.get("title", ""), is_active=True)
        messages.success(request, "Notification added.")
    return redirect("notifications_list")


@login_required
@_admin_required
def delete_notification(request, id):
    Notification.objects.filter(id=id).delete()
    return redirect("notifications_list")


# ── Analytics ─────────────────────────────────────────────────

@login_required
@_admin_required
def analytics(request):
    total_revenue = Order.objects.filter(status="Delivered").aggregate(t=Sum("total_amount"))["t"] or 0

    monthly_revenue = (
        Order.objects
        .filter(status="Delivered")
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(revenue=Sum("total_amount"))
        .order_by("month")
    )
    monthly_orders = (
        Order.objects
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(count=Count("id"))
        .order_by("month")
    )
    top_products = (
        OrderItem.objects
        .values("product__name")
        .annotate(total_qty=Sum("quantity"))
        .order_by("-total_qty")[:5]
    )
    status_counts = {
        s: Order.objects.filter(status=s).count()
        for s in ["Pending", "Confirmed", "Packed", "Shipped", "Delivered", "Cancelled"]
    }

    chart_labels        = [m["month"].strftime("%b %Y") for m in monthly_revenue if m["month"]]
    chart_revenue       = [float(m["revenue"]) for m in monthly_revenue]
    chart_order_counts  = [m["count"] for m in monthly_orders if m["month"]]

    return render(request, "web/admin/analytics.html", {
        "total_users":        User.objects.count(),
        "total_products":     Product.objects.count(),
        "total_orders":       Order.objects.count(),
        "total_revenue":      total_revenue,
        "status_counts":      status_counts,
        "top_products":       list(top_products),
        "chart_labels":       json.dumps(chart_labels),
        "chart_revenue":      json.dumps(chart_revenue),
        "chart_order_counts": json.dumps(chart_order_counts),
    })

from django.shortcuts import render, redirect
from django.contrib import messages

def about(request):
    # Pass 'active_nav' if you want to highlight the dropdown in your navbar
    context = {'active_nav': 'more'} 
    return render(request, 'web/about.html', context)

def faq(request):
    context = {'active_nav': 'more'}
    return render(request, 'web/faq.html', context)

def contact(request):
    if request.method == 'POST':
        # Retrieve form data
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        # TODO: Save to your database or send an email here
        # Example: ContactMessage.objects.create(...)
        
        # Show a success message to the user
        messages.success(request, "Thank you! Your message has been sent. We'll get back to you soon.")
        return redirect('contact')
        
    context = {'active_nav': 'more'}
    return render(request, 'web/contact.html', context)

from django.shortcuts import render, get_object_or_404
from .models import Order

def order_details(request, order_id):
    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user
    )

    return render(
        request,
        "web/order_details.html",
        {
            "order": order
        }
    )