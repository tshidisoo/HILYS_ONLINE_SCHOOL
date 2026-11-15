from django.conf import settings
from django.core.mail import send_mail

from users.models import User

from .models import Notification


def notify(users, title, body="", link="", key=""):
    """In-app always. Email only when switched on in settings (off until the owner supplies credentials)."""
    made = 0
    for u in users:
        if key and Notification.objects.filter(user=u, key=key).exists():
            continue
        Notification.objects.create(user=u, title=title, body=body, link=link, key=key)
        made += 1
        if settings.EMAIL_ENABLED and u.email:
            send_mail(title, f"{body}\n\n{link}", None, [u.email], fail_silently=True)
    return made


def staff(*roles):
    qs = User.objects.filter(is_suspended=False, role__in=roles or ["owner", "coordinator", "finance"])
    return list(qs)
