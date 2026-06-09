"""
models.py — SSD Nursery
Single authoritative model file.
Merges both versions: keeps richest fields, fixes all bugs.
"""
import random
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


# ══════════════════════════════════════════════════════════════
# USER PROFILE
# ══════════════════════════════════════════════════════════════

class UserProfile(models.Model):
    user         = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile"
    )
    phone        = models.CharField(max_length=15, unique=True, blank=True, null=True)
    address      = models.TextField(blank=True, null=True)
    area         = models.CharField(max_length=100, blank=True, null=True)
    city         = models.CharField(max_length=100, blank=True, null=True)
    state        = models.CharField(max_length=100, blank=True, null=True)
    pincode      = models.CharField(max_length=10, blank=True, null=True)
    instructions = models.TextField(blank=True, null=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} Profile"


# ══════════════════════════════════════════════════════════════
# EMAIL OTP
# ══════════════════════════════════════════════════════════════

class EmailOTP(models.Model):
    email      = models.EmailField(unique=True)
    otp        = models.CharField(max_length=6)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"OTP for {self.email}"


# ══════════════════════════════════════════════════════════════
# CATEGORY
# ══════════════════════════════════════════════════════════════

class Category(models.Model):
    name        = models.CharField(max_length=100, unique=True)
    slug        = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    image       = models.ImageField(upload_to="categories/", blank=True, null=True)
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


# ══════════════════════════════════════════════════════════════
# PRODUCT
# ══════════════════════════════════════════════════════════════

class Product(models.Model):
    category    = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="products"
    )
    name        = models.CharField(max_length=200)
    slug        = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(blank=True)
    care_guide  = models.TextField(blank=True)
    # Plant-specific care hints (optional quick fields)
    sunlight    = models.CharField(max_length=100, blank=True)
    watering    = models.CharField(max_length=100, blank=True)
    price       = models.DecimalField(max_digits=10, decimal_places=2)
    offer_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    stock       = models.PositiveIntegerField(default=0)
    image       = models.ImageField(upload_to="products/", blank=True, null=True)
    featured    = models.BooleanField(default=False)
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    @property
    def effective_price(self):
        return self.offer_price if self.offer_price else self.price

    @property
    def discount_percent(self):
        if self.offer_price and self.price:
            return int(((self.price - self.offer_price) / self.price) * 100)
        return 0


# ══════════════════════════════════════════════════════════════
# PRODUCT GALLERY
# ══════════════════════════════════════════════════════════════

class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(upload_to="products/gallery/")

    def __str__(self):
        return f"{self.product.name} — gallery image"


# ══════════════════════════════════════════════════════════════
# BANNER
# ══════════════════════════════════════════════════════════════

class Banner(models.Model):
    BANNER_TYPES = [
        ("hero",     "Hero Slide"),
        ("promo",    "Promotional"),
        ("sale",     "Sale"),
        ("SLIDER",   "Slider"),
        ("OFFER",    "Offer"),
        ("FESTIVAL", "Festival"),
    ]
    BUTTON_STYLES = [
        ("primary",   "Primary (Dark)"),
        ("secondary", "Secondary (Outlined)"),
        ("accent",    "Accent (Terracotta)"),
    ]

    image        = models.ImageField(upload_to="banners/")
    tag_text     = models.CharField(
        max_length=60, blank=True,
        help_text="Small pill label above heading e.g. '✦ New Arrivals'"
    )
    # `title` kept for backward compatibility with old admin code
    title        = models.CharField(max_length=200, blank=True)
    heading      = models.CharField(
        max_length=80, blank=True,
        help_text="Main heading (max 80 chars)"
    )
    subheading   = models.CharField(
        max_length=120, blank=True,
        help_text="Italic accent line below heading"
    )
    description  = models.CharField(
        max_length=180, blank=True,
        help_text="Short supporting description (max 180 chars)"
    )
    button_text  = models.CharField(
        max_length=40, blank=True,
        help_text="CTA button label e.g. 'Shop Now'"
    )
    button_url   = models.CharField(
        max_length=200, blank=True,
        help_text="Relative or absolute URL e.g. /shop/?sale=1"
    )
    button_style = models.CharField(
        max_length=20, choices=BUTTON_STYLES, default="primary"
    )
    banner_type  = models.CharField(
        max_length=20, choices=BANNER_TYPES, default="hero"
    )
    is_active    = models.BooleanField(default=True)
    sort_order   = models.PositiveIntegerField(
        default=0, help_text="Lower number = shown first"
    )
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "-created_at"]

    def __str__(self):
        return self.heading or self.title or f"Banner #{self.pk}"


# ══════════════════════════════════════════════════════════════
# REVIEW
# ══════════════════════════════════════════════════════════════

class Review(models.Model):
    product     = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="reviews"
    )
    user        = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="reviews"
    )
    rating      = models.PositiveSmallIntegerField(default=5)
    review      = models.TextField()
    is_approved = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)

    # NOTE: only ONE Meta class (bug in v1 — had two Meta classes)
    class Meta:
        unique_together = ("product", "user")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} — {self.product.name} ({self.rating}★)"


# ══════════════════════════════════════════════════════════════
# COUPON
# ══════════════════════════════════════════════════════════════

class Coupon(models.Model):
    DISCOUNT_TYPES = [
        ("percentage", "Percentage (%)"),
        ("flat",       "Flat (₹)"),
    ]

    code                 = models.CharField(max_length=50, unique=True)
    discount_type        = models.CharField(max_length=20, choices=DISCOUNT_TYPES)
    discount_value       = models.DecimalField(max_digits=10, decimal_places=2)
    minimum_order_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    maximum_discount     = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    expiry_date          = models.DateField(blank=True, null=True)
    is_active            = models.BooleanField(default=True)
    created_at           = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.code


# ══════════════════════════════════════════════════════════════
# COUPON USAGE
# ══════════════════════════════════════════════════════════════

class CouponUsage(models.Model):
    user    = models.ForeignKey(User, on_delete=models.CASCADE)
    coupon  = models.ForeignKey(Coupon, on_delete=models.CASCADE)
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "coupon")

    def __str__(self):
        return f"{self.user.username} — {self.coupon.code}"


# ══════════════════════════════════════════════════════════════
# DELIVERY PARTNERS  (for order tracking)
# ══════════════════════════════════════════════════════════════

DELIVERY_PARTNERS = [
    ("delhivery",  "Delhivery"),
    ("bluedart",   "Blue Dart"),
    ("dtdc",       "DTDC"),
    ("ekart",      "Ekart Logistics"),
    ("xpressbees", "XpressBees"),
    ("shadowfax",  "Shadowfax"),
    ("ecom",       "Ecom Express"),
    ("amazon",     "Amazon Logistics"),
    ("shiprocket", "Shiprocket"),
    ("other",      "Other"),
]

DELIVERY_PARTNER_URLS = {
    "delhivery":  "https://www.delhivery.com/track/package/",
    "bluedart":   "https://www.bluedart.com/tracking",
    "dtdc":       "https://www.dtdc.in/track-shipment.asp",
    "ekart":      "https://ekartlogistics.com/shipment-tracking/",
    "xpressbees": "https://www.xpressbees.com/track",
    "shadowfax":  "https://shipper.shadowfax.in/track-order/",
    "ecom":       "https://ecomexpress.in/tracking/",
    "amazon":     "https://track.amazon.in/tracking/",
    "shiprocket": "https://shiprocket.in/tracking/",
    "other":      "",
}


# ══════════════════════════════════════════════════════════════
# ORDER
# ══════════════════════════════════════════════════════════════

class Order(models.Model):
    STATUS_CHOICES = [
        ("Pending",   "Pending"),
        ("Confirmed", "Confirmed"),
        ("Packed",    "Packed"),
        ("Shipped",   "Shipped"),
        ("Delivered", "Delivered"),
        ("Returned", "Returned"),
        ("Cancelled", "Cancelled"),
    ]
    PAYMENT_CHOICES = [
        ("cod",       "Cash On Delivery"),
        ("razorpay",  "Razorpay"),
        ("online",    "Online Payment"),
    ]

    user              = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="orders"
    )
    order_number = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True
    )
    total_amount      = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount   = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status            = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="Pending"
    )
    payment_method    = models.CharField(
        max_length=50, choices=PAYMENT_CHOICES, default="cod", blank=True
    )
    # Razorpay IDs  (blank for COD orders)
    payment_id        = models.CharField(max_length=200, blank=True)
    razorpay_order_id = models.CharField(max_length=200, blank=True)
    # Delivery address snapshot
    address           = models.TextField(blank=True)
    coupon            = models.ForeignKey(
        Coupon, on_delete=models.SET_NULL, null=True, blank=True
    )
    notes             = models.TextField(blank=True)
    # Shipping / Tracking
    tracking_id       = models.CharField(max_length=100, blank=True)
    delivery_partner  = models.CharField(
        max_length=30, choices=DELIVERY_PARTNERS, blank=True, default=""
    )
    shipped_at        = models.DateTimeField(null=True, blank=True)
    delivered_at      = models.DateTimeField(null=True, blank=True)
    created_at        = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.order_number:

            while True:
                order_no = (
                    f"SSD-"
                    f"{timezone.now().strftime('%y%m')}-"
                    f"{random.randint(1000,9999)}"
                )

                if not Order.objects.filter(
                    order_number=order_no
                ).exists():
                    self.order_number = order_no
                    break

        super().save(*args, **kwargs)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.order_number} — {self.user.username}"

    @property
    def tracking_url(self):
        base = DELIVERY_PARTNER_URLS.get(self.delivery_partner, "")
        return (base + self.tracking_id) if base and self.tracking_id else ""

    @property
    def delivery_partner_display(self):
        return dict(DELIVERY_PARTNERS).get(self.delivery_partner, "")


# ══════════════════════════════════════════════════════════════
# ORDER ITEM
# ══════════════════════════════════════════════════════════════

class OrderItem(models.Model):
    order    = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="items"
    )
    product  = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price    = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} × {self.quantity}"

    @property
    def subtotal(self):
        return self.price * self.quantity


# ══════════════════════════════════════════════════════════════
# WISHLIST
# ══════════════════════════════════════════════════════════════

class Wishlist(models.Model):
    user     = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="wishlist"
    )
    product  = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="wishlisted_by"
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")

    def __str__(self):
        return f"{self.user.username} ♥ {self.product.name}"


# ══════════════════════════════════════════════════════════════
# CART ITEM
# ══════════════════════════════════════════════════════════════

class CartItem(models.Model):
    user     = models.ForeignKey(User, on_delete=models.CASCADE, related_name="cart_items")
    product  = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant  = models.ForeignKey(                                   # ← ADD
        "ProductVariant", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="cart_items"
    )
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product", "variant")           # ← UPDATED

    @property
    def subtotal(self):
        price = self.variant.price if self.variant else self.product.effective_price
        return price * self.quantity


# ══════════════════════════════════════════════════════════════
# NOTIFICATION
# ══════════════════════════════════════════════════════════════

class Notification(models.Model):
    title      = models.CharField(max_length=300)
    message    = models.TextField(blank=True)
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


# ══════════════════════════════════════════════════════════════
# CONTACT MESSAGE
# ══════════════════════════════════════════════════════════════

class ContactMessage(models.Model):
    name       = models.CharField(max_length=200)
    email      = models.EmailField()
    phone      = models.CharField(max_length=20, blank=True)
    subject    = models.CharField(max_length=100, blank=True)
    message    = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} — {self.subject}"
    
# ══════════════════════════════════════════════════════════════
# STORE SETTINGS  (singleton — always pk=1)
# ══════════════════════════════════════════════════════════════

class StoreSettings(models.Model):
    cod_enabled                = models.BooleanField(
        default=False,
        help_text="Allow Cash on Delivery for new orders."
    )
    order_modification_enabled = models.BooleanField(
        default=False,
        help_text="Allow admin to send order-modification proposals to customers."
    )
    updated_at                 = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Store Settings"
        verbose_name_plural = "Store Settings"

    def __str__(self):
        return "Store Settings"

    @classmethod
    def get(cls):
        """Always return the single settings row, creating it if needed."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


# ══════════════════════════════════════════════════════════════
# ORDER MODIFICATION REQUEST
# ══════════════════════════════════════════════════════════════

class OrderModificationRequest(models.Model):
    STATUS_CHOICES = [
        ("pending",  "Pending"),
        ("accepted", "Accepted"),
        ("declined", "Declined"),
        ("applied",  "Applied"),
        ("cancelled","Cancelled"),
    ]

    order            = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="modification_requests"
    )
    proposed_changes = models.TextField(
        help_text="Human-readable description of what will change in the order."
    )
    admin_note       = models.TextField(
        blank=True,
        help_text="Message shown to the customer in the email."
    )
    status           = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending"
    )
    # Token sent in the email so the customer can accept/decline without logging in
    token            = models.CharField(max_length=64, unique=True, blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)
    responded_at     = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"ModReq #{self.pk} — Order {self.order.order_number} [{self.status}]"

    def save(self, *args, **kwargs):
        if not self.token:
            import secrets
            self.token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)

class ProductVariant(models.Model):
    PRESET_LABELS = [
        ("lt1",  "Less than 1 year"),
        ("1yr",  "1 year"),
        ("2yr",  "2 years"),
        ("3yr",  "3 years"),
        ("4yr",  "4 years"),
        ("5yr",  "5 years"),
        ("6yr",  "6 years"),
        ("7yr",  "7 years"),
        ("8yr",  "8 years"),
        ("9yr",  "9 years"),
        ("10yr", "10 years"),
        ("custom", "Custom"),
    ]

    product      = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="variants"
    )
    label        = models.CharField(max_length=20, choices=PRESET_LABELS)
    custom_label = models.CharField(
        max_length=100, blank=True,
        help_text="Only used when label = 'custom'"
    )
    price        = models.DecimalField(max_digits=10, decimal_places=2)
    offer_price  = models.DecimalField(           # ← NEW
        max_digits=10, decimal_places=2,
        blank=True, null=True,
        help_text="Leave blank for no offer on this variant"
    )
    stock        = models.PositiveIntegerField(default=0)
    is_active    = models.BooleanField(default=True)
    sort_order   = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return f"{self.product.name} — {self.display_label}"

    @property
    def display_label(self):
        if self.label == "custom" and self.custom_label:
            return self.custom_label
        return dict(self.PRESET_LABELS).get(self.label, self.label)

    @property
    def effective_price(self):                    # ← NEW
        return self.offer_price if self.offer_price else self.price

    @property
    def discount_percent(self):                   # ← NEW
        if self.offer_price and self.price:
            return int(((self.price - self.offer_price) / self.price) * 100)
        return 0