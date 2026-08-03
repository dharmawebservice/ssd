from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Product


class StaticViewSitemap(Sitemap):
    priority = 1.0
    changefreq = "weekly"

    def items(self):
        return [
            "home",
            "shop",
            "collections",
            "about",
            "contact",
            "faq",
        ]

    def location(self, item):
        return reverse(item)


class ProductSitemap(Sitemap):
    priority = 0.9
    changefreq = "daily"

    def items(self):
        return Product.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.created_at

    def location(self, obj):
        return reverse(
            "product_detail",
            kwargs={"slug": obj.slug}
        )