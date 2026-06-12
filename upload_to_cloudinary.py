import os
import django
import cloudinary.uploader

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nursery.settings")
django.setup()

from web.models import Product, Category, Banner

uploaded = 0

def migrate_queryset(queryset, folder, label):
    global uploaded

    for obj in queryset:
        if not obj.image:
            continue

        local_path = os.path.join("media", obj.image.name)

        if not os.path.exists(local_path):
            print(f"MISSING {label}: {local_path}")
            continue

        try:
            result = cloudinary.uploader.upload(
                local_path,
                folder=folder
            )

            obj.image = result["public_id"]
            obj.save(update_fields=["image"])

            print(f"Uploaded {label}: {obj.image}")
            uploaded += 1

        except Exception as e:
            print(f"FAILED {label}: {e}")


print("Uploading Products...")
migrate_queryset(
    Product.objects.exclude(image=""),
    "media/products",
    "Product"
)

print("\nUploading Categories...")
migrate_queryset(
    Category.objects.exclude(image=""),
    "media/categories",
    "Category"
)

print("\nUploading Banners...")
migrate_queryset(
    Banner.objects.exclude(image=""),
    "media/banners",
    "Banner"
)

print("\nDONE")
print("TOTAL:", uploaded)