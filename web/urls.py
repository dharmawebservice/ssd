from django.urls import path
from . import views
from django.views.generic import RedirectView
from django.contrib.staticfiles.storage import staticfiles_storage
urlpatterns = [

    # =========================
    # Public Pages
    # =========================

    path("", views.home, name="home"),
    path("shop/", views.shop, name="shop"),
    path("collections/", views.collections, name="collections"),

    path(
        "product/<slug:slug>/",
        views.product_detail,
        name="product_detail"
    ),

    # =========================
    # Authentication
    # =========================

    path(
        "auth/",
        views.auth_page,
        name="auth"
    ),

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

    path(
        "logout/",
        views.logout_user,
        name="logout_user"
    ),

    # =========================
    # Profile
    # =========================

    path(
        "profile/",
        views.profile,
        name="profile"
    ),

    # =========================
    # Reviews
    # =========================

    path(
        "review/<int:product_id>/",
        views.submit_review,
        name="submit_review"
    ),

    path(
        "review/<int:product_id>/submit/",
        views.submit_review,
        name="submit_review"
    ),

    # =========================
    # Search API
    # =========================

    path(
        "api/search/",
        views.search_suggestions,
        name="search_suggestions"
    ),

    # =========================
    # Cart
    # =========================

    path(
        "cart/",
        views.cart_page,
        name="cart_page"
    ),

    path(
        "cart/add/",
        views.cart_add,
        name="cart_add"
    ),

    path(
        "cart/update/",
        views.cart_update,
        name="cart_update"
    ),

    path(
        "cart/remove/",
        views.cart_remove,
        name="cart_remove"
    ),

    path(
        "cart/data/",
        views.cart_data,
        name="cart_data"
    ),

    path(
        "cart/clear/",
        views.cart_clear,
        name="cart_clear"
    ),

    # =========================
    # Wishlist
    # =========================

    path(
        "wishlist/",
        views.wishlist_page,
        name="wishlist_page"
    ),

    path(
        "wishlist/toggle/",
        views.wishlist_toggle,
        name="wishlist_toggle"
    ),

    path(
        "wishlist/data/",
        views.wishlist_data,
        name="wishlist_data"
    ),

    # =========================
    # Coupons
    # =========================

    path(
        "coupon/apply/",
        views.apply_coupon,
        name="apply_coupon"
    ),

    # =========================
    # Checkout & Razorpay
    # =========================

    path(
        "checkout/",
        views.checkout,
        name="checkout"
    ),

    path(
        "checkout/create-order/",
        views.create_razorpay_order,
        name="create_razorpay_order"
    ),

    path(
        "checkout/verify-payment/",
        views.verify_razorpay_payment,
        name="verify_razorpay_payment"
    ),

    path(
        "checkout/cod/",
        views.place_cod_order,
        name="place_cod_order"
    ),

    path(
        "order/success/<int:order_id>/",
        views.order_success,
        name="order_success"
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

    path(
        "dashboard/analytics/",
        views.analytics,
        name="analytics"
    ),

    # =========================
    # Users
    # =========================

    path(
        "dashboard/users/",
        views.users_list,
        name="users_list"
    ),
    

    # =========================
    # Categories
    # =========================

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
        "dashboard/categories/edit/<int:id>/",
        views.edit_category,
        name="edit_category"
    ),

    path(
        "dashboard/categories/toggle/<int:id>/",
        views.toggle_category,
        name="toggle_category"
    ),

    path(
        "dashboard/categories/delete/<int:id>/",
        views.delete_category,
        name="delete_category"
    ),

    # =========================
    # Products
    # =========================

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
        "dashboard/products/edit/<int:id>/",
        views.edit_product,
        name="edit_product"
    ),

    path(
        "dashboard/products/toggle/<int:id>/",
        views.toggle_product,
        name="toggle_product"
    ),

    path(
        "dashboard/products/delete/<int:id>/",
        views.delete_product,
        name="delete_product"
    ),

    # =========================
    # Orders
    # =========================

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

    # =========================
    # Coupons Admin
    # =========================

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

    # =========================
    # Reviews Admin
    # =========================

    path(
        "dashboard/reviews/",
        views.reviews_list,
        name="reviews_list"
    ),

    path(
        "dashboard/reviews/delete/<int:id>/",
        views.delete_review,
        name="delete_review"
    ),

    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('faq/', views.faq, name='faq'),

    # =========================
    # Banners
    # =========================

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
        "dashboard/banners/edit/<int:id>/",
        views.edit_banner,
        name="edit_banner"
    ),

    path(
        "dashboard/banners/toggle/<int:id>/",
        views.toggle_banner,
        name="toggle_banner"
    ),

    path(
        "dashboard/banners/delete/<int:id>/",
        views.delete_banner,
        name="delete_banner"
    ),

    # =========================
    # Notifications
    # =========================

    path(
        "dashboard/notifications/",
        views.notifications_list,
        name="notifications_list"
    ),

    path(
        "dashboard/notifications/add/",
        views.add_notification,
        name="add_notification"
    ),

    path(
        "dashboard/notifications/delete/<int:id>/",
        views.delete_notification,
        name="delete_notification"
    ),

    path(
        "review/<int:product_id>/submit/",
        views.submit_review,
        name="submit_review"
    ),

    path(
    "order-details/<int:order_id>/",
    views.order_details,
    name="order_details"
),

path(
"contact-submit/",
views.contact_submit,
name="contact_submit"
),

path(
        'favicon.ico',
            RedirectView.as_view(
                url=staticfiles_storage.url('favicon.ico'),
                permanent=True
            ),
        ),

# ════════════════════════════════════════
# STORE SETTINGS
# ════════════════════════════════════════

path(
    "dashboard/store-settings/",
    views.store_settings,
    name="store_settings"
),

path(
    "dashboard/store-settings/send-modification-request/",
    views.send_modification_request,
    name="send_modification_request"
),

path(
    "dashboard/store-settings/apply-order-modification/<int:req_id>/",
    views.apply_order_modification,
    name="apply_order_modification"
),

path(
    "dashboard/store-settings/cancel-modification-request/<int:req_id>/",
    views.cancel_modification_request,
    name="cancel_modification_request"
),
# ════════════════════════════════════════
# CUSTOMER ACCEPT / DECLINE LINKS
# ════════════════════════════════════════

path(
    "order/modification/<str:token>/<str:action>/",
    views.modification_response,
    name="modification_response"
),

path('admin-panel/emergency-order/lookup/', views.emergency_order_lookup, name='emergency_order_lookup'),
path('admin-panel/emergency-order/update/', views.emergency_order_update, name='emergency_order_update'),
path(
    "admin-panel/emergency-product-search/",
    views.emergency_product_search,
    name="emergency_product_search"
),

path("product/<int:product_id>/variant-price/", views.get_variant_price, name="get_variant_price"),
path("admin-panel/products/<int:product_id>/variants/", views.manage_variants, name="manage_variants"),
]