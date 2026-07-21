"""
Per the notebook plan: "If department isn't working, there is a timeframe...
admin should warn them or force them to work... it should be shorter during
an emergency."

Run this periodically (e.g. via cron or `while true; do ...; sleep 3600; done`
for the demo) to flag stale complaints and notify admins.

Usage:
    python manage.py check_sla
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import User
from complaints.models import Complaint, Notification

NORMAL_SLA_HOURS = 48
EMERGENCY_SLA_HOURS = 6


class Command(BaseCommand):
    help = "Warns admins about complaints that a department hasn't acted on within the SLA time frame."

    def handle(self, *args, **options):
        now = timezone.now()
        admins = User.objects.filter(role=User.Role.ADMIN) | User.objects.filter(is_superuser=True)
        warned = 0

        stale_qs = Complaint.objects.filter(status=Complaint.Status.PENDING)

        for complaint in stale_qs:
            sla_hours = EMERGENCY_SLA_HOURS if complaint.is_emergency else NORMAL_SLA_HOURS
            deadline = complaint.created_at + timedelta(hours=sla_hours)

            if now > deadline:
                already_warned = Notification.objects.filter(
                    complaint=complaint, kind=Notification.Kind.SLA_WARNING
                ).exists()
                if already_warned:
                    continue

                dept_name = complaint.department.name if complaint.department else "Unassigned"
                msg = (
                    f"Complaint #{complaint.id} ('{complaint.title}') assigned to "
                    f"{dept_name} has been pending past its "
                    f"{'EMERGENCY ' if complaint.is_emergency else ''}SLA of {sla_hours}h."
                )
                for admin in admins:
                    Notification.objects.create(
                        recipient=admin, complaint=complaint,
                        kind=Notification.Kind.SLA_WARNING, message=msg,
                    )
                warned += 1
                self.stdout.write(self.style.WARNING(msg))

        self.stdout.write(self.style.SUCCESS(f"\nDone. {warned} complaint(s) flagged."))
