from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


# ==========================================
# USER PROFILE
# ==========================================

class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile"
    )

    phone = models.CharField(
        max_length=15,
        unique=True,
        blank=True,
        null=True
    )

    address = models.TextField(
        blank=True,
        null=True
    )

    area = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    city = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    state = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    pincode = models.CharField(
        max_length=10,
        blank=True,
        null=True
    )

    instructions = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.user.username} Profile"


# ==========================================
# EMAIL OTP
# ==========================================

class EmailOTP(models.Model):
    email = models.EmailField(
        unique=True
    )

    otp = models.CharField(
        max_length=6
    )

    created_at = models.DateTimeField(
        default=timezone.now
    )

    def __str__(self):
        return f"OTP for {self.email}"


# ==========================================
# CATEGORY
# ==========================================

class Category(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True
    )

    slug = models.SlugField(
        max_length=120,
        unique=True,
        blank=True
    )

    image = models.ImageField(
        upload_to="categories/",
        blank=True,
        null=True
    )

    description = models.TextField(
        blank=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


# ==========================================
# PRODUCT
# ==========================================

class Product(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="products"
    )

    name = models.CharField(
        max_length=200
    )

    slug = models.SlugField(
        max_length=220,
        unique=True,
        blank=True
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    offer_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True
    )

    stock = models.PositiveIntegerField(
        default=0
    )

    image = models.ImageField(
        upload_to="products/",
        blank=True,
        null=True
    )

    description = models.TextField(
        blank=True
    )

    care_guide = models.TextField(
        blank=True
    )

    sunlight = models.CharField(
        max_length=100,
        blank=True
    )

    watering = models.CharField(
        max_length=100,
        blank=True
    )

    featured = models.BooleanField(
        default=False
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

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
            return int(
                ((self.price - self.offer_price) / self.price) * 100
            )
        return 0


# ==========================================
# PRODUCT GALLERY
# ==========================================

class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images"
    )

    image = models.ImageField(
        upload_to="products/gallery/"
    )

    def __str__(self):
        return self.product.name


# ==========================================
# BANNERS
# ==========================================

class Banner(models.Model):

    BANNER_TYPES = [
        ("SLIDER", "Slider"),
        ("OFFER", "Offer"),
        ("FESTIVAL", "Festival"),
    ]

    title = models.CharField(
        max_length=200,
        blank=True
    )

    image = models.ImageField(
        upload_to="banners/"
    )

    banner_type = models.CharField(
        max_length=20,
        choices=BANNER_TYPES,
        default="SLIDER"
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.title or f"Banner {self.id}"


# ==========================================
# REVIEWS
# ==========================================

class Review(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reviews"
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="reviews"
    )

    rating = models.PositiveSmallIntegerField(
        default=5
    )

    review = models.TextField()

    is_approved = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        unique_together = ("product", "user")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"


# ==========================================
# COUPONS
# ==========================================

class Coupon(models.Model):

    DISCOUNT_TYPES = [
        ("PERCENTAGE", "Percentage"),
        ("FLAT", "Flat"),
    ]

    code = models.CharField(
        max_length=50,
        unique=True
    )

    discount_type = models.CharField(
        max_length=20,
        choices=DISCOUNT_TYPES
    )

    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    minimum_order_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    maximum_discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True
    )

    expiry_date = models.DateField(
        blank=True,
        null=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.code


# ==========================================
# COUPON USAGE
# ==========================================

class CouponUsage(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.CASCADE
    )

    used_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        unique_together = ("user", "coupon")

    def __str__(self):
        return f"{self.user.username} - {self.coupon.code}"


# ==========================================
# ORDERS
# ==========================================

class Order(models.Model):

    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Confirmed", "Confirmed"),
        ("Packed", "Packed"),
        ("Shipped", "Shipped"),
        ("Delivered", "Delivered"),
        ("Cancelled", "Cancelled"),
    ]

    PAYMENT_CHOICES = [
        ("COD", "Cash On Delivery"),
        ("ONLINE", "Online Payment"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="orders"
    )

    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_CHOICES,
        default="COD"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Pending"
    )

    address = models.TextField(
        blank=True
    )

    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.id}"


# ==========================================
# ORDER ITEMS
# ==========================================

class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items"
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE
    )

    quantity = models.PositiveIntegerField(
        default=1
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    @property
    def subtotal(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"


# ==========================================
# NOTIFICATIONS
# ==========================================

class Notification(models.Model):
    title = models.CharField(
        max_length=300
    )

    message = models.TextField(
        blank=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.title