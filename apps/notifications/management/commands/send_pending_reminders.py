"""
Management command: send_pending_reminders

Sends reminder emails to clients who have pending actions.
Schedule via cPanel cron (e.g. daily at 9 AM):
  0 9 * * * /path/to/python /path/to/manage.py send_pending_reminders

Thresholds:
  - draft           → 7+ days since last update (not yet submitted)
  - awaiting_confirmation  → 2+ days (consultant sent for confirmation)
  - awaiting_client_review → 3+ days (review pending client action)
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from apps.tax_forms.models import TaxSubmission
from apps.notifications.email_utils import _build_html, _get_portal_url
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


THRESHOLDS = {
    'draft': (7, 'action_required'),
    'awaiting_confirmation': (2, 'action_required'),
    'awaiting_client_review': (3, 'action_required'),
}

MESSAGES = {
    'draft': (
        'Your Tax Return Is Waiting — Action Needed',
        [
            'Your income tax return for Y/A 2025/2026 has been started but not yet submitted to DPR Consultants.',
            'Please log in to the portal and complete your tax form so our team can begin processing your return.',
            'If you have any questions or need assistance, please contact your assigned consultant.',
        ],
    ),
    'awaiting_confirmation': (
        'Please Confirm Your Tax Calculation',
        [
            'Your consultant has completed the tax calculation for your Y/A 2025/2026 return and it is now awaiting your confirmation.',
            'Please log in to the portal to review the calculation and provide your confirmation to proceed.',
            'Timely confirmation ensures your return can be filed within the required deadline.',
        ],
    ),
    'awaiting_client_review': (
        'Your Tax Documents Are Ready for Review',
        [
            'Your consultant has prepared the final tax documents for your Y/A 2025/2026 submission. They are now ready for your review.',
            'Please log in to the portal to review and acknowledge the documents.',
            'Your prompt review will allow us to complete the filing process without delay.',
        ],
    ),
}


class Command(BaseCommand):
    help = 'Send reminder emails to clients with pending tax form actions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print what would be sent without actually sending emails',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        now = timezone.now()
        total_sent = 0

        for status, (days, _) in THRESHOLDS.items():
            cutoff = now - timedelta(days=days)
            submissions = (
                TaxSubmission.objects
                .filter(status=status, updated_at__lte=cutoff)
                .select_related('client', 'tax_year')
            )

            title, paragraphs = MESSAGES[status]

            for sub in submissions:
                client = sub.client
                if not client.email:
                    continue

                recipient_name = client.get_full_name().strip() or client.email.split('@')[0].capitalize()
                tax_year_label = str(sub.tax_year) if sub.tax_year else 'Y/A 2025/2026'

                # Personalise paragraphs with the specific tax year
                personalised = [p.replace('Y/A 2025/2026', tax_year_label) for p in paragraphs]

                if dry_run:
                    self.stdout.write(
                        f'[DRY RUN] Would email {client.email} — "{title}" '
                        f'(status={status}, last_updated={sub.updated_at.date()})'
                    )
                    continue

                html_body = _build_html(
                    recipient_name=recipient_name,
                    title=title,
                    message_paragraphs=personalised,
                    action_url=_get_portal_url(),
                    action_label='Open Tax Portal',
                )
                plain_body = (
                    f'Dear {recipient_name},\n\n'
                    + '\n\n'.join(personalised)
                    + f'\n\nOpen the portal: {_get_portal_url()}'
                    + '\n\n— DPR Tax Management System'
                )

                try:
                    msg = EmailMultiAlternatives(
                        subject=f'[DPR TMS] {title}',
                        body=plain_body,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=[client.email],
                    )
                    msg.attach_alternative(html_body, 'text/html')
                    msg.send(fail_silently=False)
                    total_sent += 1
                    logger.info('Reminder sent to %s (submission %s)', client.email, sub.id)
                    self.stdout.write(f'  Sent to {client.email} — {title}')
                except Exception as exc:
                    logger.warning('Failed reminder to %s: %s', client.email, exc)
                    self.stdout.write(self.style.WARNING(f'  FAILED {client.email}: {exc}'))

        if not dry_run:
            self.stdout.write(self.style.SUCCESS(f'Done. {total_sent} reminder(s) sent.'))
