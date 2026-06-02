from django.urls import path
from . import views

urlpatterns = [

    # =========================
    # Public Pages
    # =========================

    path("", views.home, name="home"),

    path(
        "auth/",
        views.auth_page,
        name="auth"
    ),

    path(
        "profile/",
        views.profile,
        name="profile"
    ),

    path(
        "logout/",
        views.logout_user,
        name="logout_user"
    ),

    # =========================
    # Authentication
    # =========================

    path(
        "send-otp/",
        views.send_signup_otp,
        name="send_otp"
    ),

    path(
        "verify-otp/",
        views.verify_signup_otp,
        name="verify_otp"
    ),

    path(
        "resend-otp/",
        views.resend_otp,
        name="resend_otp"
    ),

    path(
        "login-user/",
        views.login_user,
        name="login_user"
    ),

    path(
        "save-details/",
        views.save_details,
        name="save_details"
    ),

    # =========================
    # Location API
    # =========================

    path(
        "reverse-geocode/",
        views.reverse_geocode,
        name="reverse_geocode"
    ),

    # =========================
    # Admin Dashboard
    # =========================

    path(
        "dashboard/",
        views.admin_dashboard,
        name="admin_dashboard"
    ),

    # Users

    path(
        "dashboard/users/",
        views.users_list,
        name="users_list"
    ),

    # Categories

    path(
        "dashboard/categories/",
        views.category_list,
        name="category_list"
    ),

    path(
        "dashboard/categories/add/",
        views.add_category,
        name="add_category"
    ),

    path(
        "dashboard/categories/delete/<int:id>/",
        views.delete_category,
        name="delete_category"
    ),

    # Products

    path(
        "dashboard/products/",
        views.product_list,
        name="product_list"
    ),

    path(
        "dashboard/products/add/",
        views.add_product,
        name="add_product"
    ),

    path(
        "dashboard/products/delete/<int:id>/",
        views.delete_product,
        name="delete_product"
    ),

    # Orders

    path(
        "dashboard/orders/",
        views.order_list,
        name="order_list"
    ),

    path(
        "dashboard/orders/update/<int:order_id>/",
        views.update_order_status,
        name="update_order_status"
    ),

    # Coupons

    path(
        "dashboard/coupons/",
        views.coupon_list,
        name="coupon_list"
    ),

    path(
        "dashboard/coupons/add/",
        views.add_coupon,
        name="add_coupon"
    ),

    path(
        "dashboard/coupons/delete/<int:id>/",
        views.delete_coupon,
        name="delete_coupon"
    ),

    # Reviews

    path(
        "dashboard/reviews/",
        views.reviews_list,
        name="reviews_list"
    ),

    path(
        "dashboard/reviews/approve/<int:id>/",
        views.approve_review,
        name="approve_review"
    ),

    path(
        "dashboard/reviews/delete/<int:id>/",
        views.delete_review,
        name="delete_review"
    ),

    # Banners

    path(
        "dashboard/banners/",
        views.banners_list,
        name="banners_list"
    ),

    path(
        "dashboard/banners/add/",
        views.add_banner,
        name="add_banner"
    ),

    path(
        "dashboard/banners/delete/<int:id>/",
        views.delete_banner,
        name="delete_banner"
    ),

    # Analytics

    path(
        "dashboard/analytics/",
        views.analytics,
        name="analytics"
    ),
]