from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from web.sitemaps import StaticViewSitemap, ProductSitemap
from django.contrib.sitemaps.views import sitemap as django_sitemap
from django.views.decorators.http import condition
from web.sitemaps import (
    StaticViewSitemap,
    ProductSitemap,
)

sitemaps = {
    "static": StaticViewSitemap,
    "products": ProductSitemap,
}

@condition(etag_func=None)
def sitemap(request, **kwargs):
    response = django_sitemap(request, **kwargs)
    response.headers.pop("X-Robots-Tag", None)
    return response

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("web.urls")),

    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),

    path(
    "robots.txt",
    TemplateView.as_view(
        template_name="robots.txt",
        content_type="text/plain",
    ),
),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)