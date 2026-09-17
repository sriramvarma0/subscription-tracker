from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from flask import request, g

def get_user_timezone():
    """
    Retrieves the user's timezone from cookie or request args, falling back to local system timezone or UTC.
    """
    tz_name = None
    if request:
        tz_name = request.cookies.get('user_timezone')
        if not tz_name and request.args.get('tz'):
            tz_name = request.args.get('tz')

    if tz_name:
        try:
            return ZoneInfo(tz_name.strip())
        except (ZoneInfoNotFoundError, ValueError, KeyError):
            pass

    # Fall back to server system local timezone or UTC
    try:
        sys_tz = datetime.now().astimezone().tzinfo
        if sys_tz:
            return sys_tz
    except Exception:
        pass
    return timezone.utc

def get_user_today(override_tz=None) -> date:
    """
    Returns today's date in the user's local timezone.
    """
    if override_tz:
        if isinstance(override_tz, str):
            try:
                return datetime.now(ZoneInfo(override_tz)).date()
            except Exception:
                pass
        elif hasattr(override_tz, 'utcoffset'):
            return datetime.now(override_tz).date()

    if hasattr(g, 'user_timezone') and g.user_timezone:
        tz = g.user_timezone
    else:
        tz = get_user_timezone()

    return datetime.now(tz).date()
