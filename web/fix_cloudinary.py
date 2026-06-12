import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nursery.settings")
django.setup()

from django.core.files import File
from web.models import Product, Category, Banner

def migrate(queryset, label):
    for obj in queryset:
        if not obj.image:
            continue

        try:
            old_name = obj.image.name

            if old_name.startswith("media/"):
                print("Skipping:", old_name)
                continue

            local_path = os.path.join("media", old_name)

            if not os.path.exists(local_path):
                print("Missing:", local_path)
                continue

            with open(local_path, "rb") as f:
                obj.image.save(
                    os.path.basename(local_path),
                    File(f),
                    save=True
                )

            print("Uploaded", label, obj.id)

        except Exception as e:
            print("FAILED", obj.id, e)

migrate(Product.objects.all(), "Product")
migrate(Category.objects.all(), "Category")
migrate(Banner.objects.all(), "Banner")

print("DONE")