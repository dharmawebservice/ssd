from .models import Notification


def user_profile(request):
    """Inject notifications into every template context."""
    notifications = Notification.objects.filter(is_active=True).order_by("-id")[:5]
    return {"notifications": notifications}