import logging
from django.core.mail import EmailMultiAlternatives
from django.conf import settings

logger = logging.getLogger(__name__)


def _get_portal_url():
    return getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')


def _build_html(recipient_name, title, message_paragraphs, action_url=None, action_label='Open Tax Portal'):
    """Render a branded HTML email body."""
    action_block = ''
    if action_url:
        action_block = f'''
        <table cellpadding="0" cellspacing="0" style="margin:28px 0 8px;">
          <tr>
            <td style="background-color:#F5C518;border-radius:8px;">
              <a href="{action_url}"
                 style="display:inline-block;padding:13px 28px;color:#0a0a0a;font-weight:700;
                        font-size:14px;text-decoration:none;letter-spacing:0.3px;font-family:Arial,sans-serif;">
                {action_label} &rarr;
              </a>
            </td>
          </tr>
        </table>'''

    paragraphs_html = ''.join(
        f'<p style="margin:0 0 14px;color:#bbbbbb;font-size:14px;line-height:1.7;'
        f'font-family:Arial,Helvetica,sans-serif;">{p}</p>'
        for p in message_paragraphs
    )

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>{title}</title>
</head>
<body style="margin:0;padding:0;background-color:#0a0a0a;">
<table width="100%" cellpadding="0" cellspacing="0" role="presentation"
       style="background-color:#0a0a0a;padding:40px 16px;">
  <tr>
    <td align="center">
      <table width="600" cellpadding="0" cellspacing="0" role="presentation"
             style="max-width:600px;width:100%;">

        <!-- ── Header ── -->
        <tr>
          <td style="background-color:#141414;border-radius:16px 16px 0 0;
                     padding:26px 40px 22px;border-bottom:2px solid #F5C518;">
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td>
                  <p style="margin:0;color:#F5C518;font-size:20px;font-weight:700;
                            letter-spacing:0.5px;font-family:Arial,sans-serif;">
                    DPR CONSULTANTS
                  </p>
                  <p style="margin:4px 0 0;color:#666666;font-size:11px;
                            letter-spacing:1.5px;text-transform:uppercase;
                            font-family:Arial,sans-serif;">
                    Tax Management System
                  </p>
                </td>
                <td align="right" valign="middle">
                  <span style="display:inline-block;background-color:#F5C518;color:#0a0a0a;
                               font-size:10px;font-weight:700;padding:4px 12px;
                               border-radius:20px;letter-spacing:0.5px;
                               font-family:Arial,sans-serif;">
                    Y/A 2025/2026
                  </span>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- ── Body ── -->
        <tr>
          <td style="background-color:#141414;padding:36px 40px 32px;">
            <p style="margin:0 0 6px;color:#777777;font-size:13px;
                      font-family:Arial,sans-serif;">
              Dear {recipient_name},
            </p>
            <h1 style="margin:0 0 22px;color:#ffffff;font-size:20px;font-weight:600;
                       line-height:1.35;font-family:Arial,sans-serif;">
              {title}
            </h1>
            {paragraphs_html}
            {action_block}
          </td>
        </tr>

        <!-- ── Divider ── -->
        <tr>
          <td style="background-color:#141414;padding:0 40px;">
            <hr style="border:none;border-top:1px solid #222222;margin:0;">
          </td>
        </tr>

        <!-- ── Footer ── -->
        <tr>
          <td style="background-color:#0f0f0f;border-radius:0 0 16px 16px;padding:22px 40px;">
            <p style="margin:0 0 3px;color:#555555;font-size:12px;font-weight:600;
                      font-family:Arial,sans-serif;">
              DPR Consultants (Pvt) Ltd
            </p>
            <p style="margin:0 0 2px;color:#444444;font-size:11px;font-family:Arial,sans-serif;">
              tms@dpr.lk
            </p>
            <p style="margin:12px 0 0;color:#333333;font-size:11px;line-height:1.5;
                      font-family:Arial,sans-serif;">
              This is an automated message from the DPR Tax Management System.
              Please do not reply to this email. If you have questions, contact your
              assigned consultant directly.
            </p>
          </td>
        </tr>

      </table>
    </td>
  </tr>
</table>
</body>
</html>'''


def send_notification_email(notification):
    """
    Send a professional HTML email for a Notification instance.
    Called automatically via post_save signal whenever a Notification is created.
    Errors are logged as warnings — never raise so in-app notifications still save.
    """
    recipient = notification.recipient
    if not recipient.email:
        return

    recipient_name = recipient.get_full_name().strip() or recipient.email.split('@')[0].capitalize()

    # Split the plain-text message into paragraphs for the HTML body
    paragraphs = [line.strip() for line in notification.message.split('\n') if line.strip()]

    html_body = _build_html(
        recipient_name=recipient_name,
        title=notification.title,
        message_paragraphs=paragraphs,
        action_url=_get_portal_url(),
        action_label='Open Tax Portal',
    )

    subject = f'[DPR TMS] {notification.title}'
    plain_body = f'Dear {recipient_name},\n\n{notification.message}\n\nOpen the portal: {_get_portal_url()}\n\n— DPR Tax Management System'

    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=plain_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient.email],
        )
        msg.attach_alternative(html_body, 'text/html')
        msg.send(fail_silently=False)
        logger.info('Email sent to %s — %s', recipient.email, notification.title)
    except Exception as exc:
        logger.warning('Failed to send email to %s (%s): %s', recipient.email, notification.title, exc)
