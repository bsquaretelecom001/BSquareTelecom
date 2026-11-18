from django.db.models import Q
from django.utils import timezone

from .models import Announcement


def active_announcements(request):
    now = timezone.now()

    announcements = Announcement.objects.filter(
        is_published=True,
        starts_at__lte=now,
    ).filter(
        Q(ends_at__isnull=True) | Q(ends_at__gte=now)
    )

    return {
        "active_announcements": announcements,
    }