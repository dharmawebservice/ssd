from .models import Notification
from .models import CartItem

def user_profile(request):
    """Inject notifications into every template context."""
    notifications = Notification.objects.filter(is_active=True).order_by("-id")[:5]
    return {"notifications": notifications}


def cart_count(request):

    count = 0

    if request.user.is_authenticated:
        count = sum(
            i.quantity
            for i in CartItem.objects.filter(user=request.user)
        )

    return {
        "cart_count": count
    }

