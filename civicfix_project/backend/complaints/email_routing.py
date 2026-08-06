"""Email delivery for complaints after AI/category department routing."""

import logging

from django.conf import settings
from django.core.mail import EmailMessage
from django.utils import timezone


logger = logging.getLogger(__name__)


def _complaint_body(complaint):
    urgency = "EMERGENCY" if complaint.is_emergency else "Standard priority"
    coordinates = "Not provided"
    if complaint.latitude is not None and complaint.longitude is not None:
        coordinates = f"{complaint.latitude}, {complaint.longitude}"
    dashboard_url = (
        f"{settings.FRONTEND_BASE_URL.rstrip('/')}/department/complaint.html?id={complaint.id}"
    )
    return "\n".join(
        [
            f"CivicFix has routed complaint #{complaint.id} to {complaint.department.name}.",
            "",
            f"Priority: {urgency}",
            f"Emergency confidence: {complaint.emergency_confidence:.0%}",
            f"Category: {complaint.get_category_display()}",
            f"Title: {complaint.title}",
            f"Description: {complaint.description}",
            f"Address: {complaint.address or 'Not provided'}",
            f"Coordinates: {coordinates}",
            f"Reported by: {complaint.citizen.email}",
            f"Submitted: {complaint.created_at.astimezone().strftime('%Y-%m-%d %H:%M %Z')}",
            "",
            f"Open the department dashboard: {dashboard_url}",
            "",
            "This message was generated automatically after CivicFix categorized and routed the complaint.",
        ]
    )


def send_department_complaint_email(complaint, force=False):
    """Send one routed complaint email and persist a non-sensitive audit result."""
    if complaint.department_email_sent_at and not force:
        return True

    recipient = ""
    if complaint.department:
        recipient = (complaint.department.contact_email or "").strip()
    complaint.department_email_recipient = recipient

    if not settings.SEND_DEPARTMENT_EMAILS:
        complaint.department_email_error = "Department email delivery is disabled."
        complaint.save(update_fields=["department_email_recipient", "department_email_error"])
        return False

    if not recipient:
        complaint.department_email_error = "The routed department has no contact email."
        complaint.save(update_fields=["department_email_recipient", "department_email_error"])
        return False

    if recipient.lower().endswith(".local"):
        complaint.department_email_error = (
            "The routed department still uses a placeholder .local email address."
        )
        complaint.save(update_fields=["department_email_recipient", "department_email_error"])
        return False

    priority = "EMERGENCY - " if complaint.is_emergency else ""
    subject = f"[CivicFix] {priority}Complaint #{complaint.id}: {complaint.title}"[:240].upper()
    message = EmailMessage(
        subject=subject,
        body=_complaint_body(complaint),
        to=[recipient],
    )
    if complaint.photo:
        try:
            message.attach_file(complaint.photo.path)
        except (OSError, ValueError, NotImplementedError) as exc:
            logger.warning("Could not attach photo for complaint %s: %s", complaint.id, exc)

    try:
        sent_count = message.send(fail_silently=False)
        if sent_count != 1:
            raise RuntimeError("The email backend did not confirm delivery.")
    except Exception as exc:
        logger.exception("Department email failed for complaint %s", complaint.id)
        complaint.department_email_sent_at = None
        complaint.department_email_error = str(exc)[:500] or exc.__class__.__name__
        complaint.save(
            update_fields=[
                "department_email_recipient",
                "department_email_sent_at",
                "department_email_error",
            ]
        )
        return False

    complaint.department_email_sent_at = timezone.now()
    complaint.department_email_error = ""
    complaint.save(
        update_fields=[
            "department_email_recipient",
            "department_email_sent_at",
            "department_email_error",
        ]
    )
    return True
