import logging
import re
import time

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

_LOGIN_CACHE_KEY = 'esms_login_token'


def _normalize_msisdn(raw):
    """
    Normalize a Sri Lankan mobile number to the 9-digit format eSMS expects
    (e.g. "714551682"). Accepts local (0771234567), international
    (+94771234567 / 94771234567) or bare 9-digit input. Returns None if the
    number can't be normalized to a valid-looking mobile number.
    """
    if not raw:
        return None
    digits = re.sub(r'\D', '', str(raw))
    if digits.startswith('94') and len(digits) == 11:
        digits = digits[2:]
    elif digits.startswith('0') and len(digits) == 10:
        digits = digits[1:]
    if len(digits) == 9 and digits[0] == '7':
        return digits
    return None


def _login_for_token():
    """Username/password login fallback — only used if ESMS_API_KEY is not set."""
    cached = cache.get(_LOGIN_CACHE_KEY)
    if cached:
        return cached

    if not (settings.ESMS_USERNAME and settings.ESMS_PASSWORD):
        logger.warning('eSMS: no ESMS_API_KEY or ESMS_USERNAME/ESMS_PASSWORD configured — cannot send SMS.')
        return None

    try:
        resp = requests.post(
            settings.ESMS_LOGIN_URL,
            json={'username': settings.ESMS_USERNAME, 'password': settings.ESMS_PASSWORD},
            headers={'Content-Type': 'application/json'},
            timeout=10,
        )
        data = resp.json()
    except Exception as exc:
        logger.warning('eSMS: login request failed: %s', exc)
        return None

    if data.get('status') != 'success' or not data.get('token'):
        logger.warning('eSMS: login failed — %s', data.get('comment'))
        return None

    token = data['token']
    # Cache for slightly less than the reported expiration (default 12h) so we
    # refresh proactively instead of hitting a 100 (expired token) error.
    ttl = max(60, int(data.get('expiration') or 43200) - 300)
    cache.set(_LOGIN_CACHE_KEY, token, timeout=ttl)
    return token


def _get_token(force_refresh=False):
    if settings.ESMS_API_KEY:
        return settings.ESMS_API_KEY
    if force_refresh:
        cache.delete(_LOGIN_CACHE_KEY)
    return _login_for_token()


def send_sms(mobile_numbers, message):
    """
    Send an SMS to one or more Sri Lankan mobile numbers via the Dialog eSMS API.
    Returns True if the campaign was accepted by eSMS, False otherwise.
    Never raises — failures are logged so callers (e.g. notification creation)
    are never blocked by an SMS delivery problem.
    """
    if not getattr(settings, 'ESMS_ENABLED', True):
        return False

    normalized = [n for n in (_normalize_msisdn(m) for m in mobile_numbers) if n]
    if not normalized:
        logger.info('eSMS: no valid mobile numbers to send to (raw=%s)', mobile_numbers)
        return False

    token = _get_token()
    if not token:
        return False

    payload = {
        'msisdn': [{'mobile': m} for m in normalized],
        'message': message[:600],  # keep well within multi-part limits
        'transaction_id': int(time.time() * 1000),
        'payment_method': 0,
    }
    if settings.ESMS_SENDER_ADDRESS:
        payload['sourceAddress'] = settings.ESMS_SENDER_ADDRESS

    def _post(bearer_token):
        return requests.post(
            settings.ESMS_SEND_URL,
            json=payload,
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {bearer_token}',
            },
            timeout=10,
        )

    try:
        resp = _post(token)
        data = resp.json()
    except Exception as exc:
        logger.warning('eSMS: send request failed for %s: %s', normalized, exc)
        return False

    # Token expired (errCode 100) — refresh once and retry, but only when we're
    # managing our own login token (a static ESMS_API_KEY can't be refreshed here).
    if data.get('errCode') == 100 and not settings.ESMS_API_KEY:
        token = _get_token(force_refresh=True)
        if not token:
            return False
        try:
            resp = _post(token)
            data = resp.json()
        except Exception as exc:
            logger.warning('eSMS: retry send request failed for %s: %s', normalized, exc)
            return False

    if data.get('status') == 'success':
        logger.info('eSMS: sent to %s — %s', normalized, data.get('comment'))
        return True

    logger.warning('eSMS: send failed for %s — %s (errCode=%s)', normalized, data.get('comment'), data.get('errCode'))
    return False
