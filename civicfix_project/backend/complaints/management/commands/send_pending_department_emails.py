from django.core.management.base import BaseCommand

from complaints.email_routing import send_department_complaint_email
from complaints.models import Complaint


class Command(BaseCommand):
    help = "Retry department emails that have not yet been delivered."

    def handle(self, *args, **options):
        pending = Complaint.objects.filter(
            department_email_sent_at__isnull=True,
            department__isnull=False,
        ).select_related("department", "citizen")
        sent = failed = 0
        for complaint in pending:
            if send_department_complaint_email(complaint):
                sent += 1
            else:
                failed += 1
        self.stdout.write(self.style.SUCCESS(f"Sent: {sent}; still pending/failed: {failed}"))
