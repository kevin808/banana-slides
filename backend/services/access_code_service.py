"""Service helpers for access code verification and quota handling."""
import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError

from models import AccessCode, db

logger = logging.getLogger(__name__)


def hash_code(code: str) -> str:
    """Hash plaintext code for storage and lookup."""
    return hashlib.sha256(code.strip().encode('utf-8')).hexdigest()


def _parse_expire_time(value) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    if text.endswith('Z'):
        text = text[:-1] + '+00:00'
    try:
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo:
            return parsed.astimezone(timezone.utc).replace(tzinfo=None)
        return parsed
    except ValueError:
        return None


def _is_expired(expires_at: Optional[datetime]) -> bool:
    if not expires_at:
        return False
    if expires_at.tzinfo:
        return expires_at <= datetime.now(timezone.utc)
    return expires_at <= datetime.utcnow()


def verify_member_code(code: str) -> Optional[AccessCode]:
    """Verify member access code and return model when valid."""
    text = (code or '').strip()
    if not text:
        return None
    try:
        code_obj = AccessCode.query.filter_by(code_hash=hash_code(text)).first()
    except SQLAlchemyError:
        db.session.rollback()
        return None
    if not code_obj:
        return None
    if not code_obj.is_active or _is_expired(code_obj.expires_at):
        return None
    return code_obj


def is_member_access_enabled() -> bool:
    """Whether member-code protection should be enabled."""
    try:
        now = datetime.utcnow()
        code_obj = AccessCode.query.filter(
            AccessCode.is_active.is_(True),
            or_(AccessCode.expires_at.is_(None), AccessCode.expires_at > now),
        ).first()
        return code_obj is not None
    except SQLAlchemyError:
        db.session.rollback()
        return False


def has_quota(code_obj: AccessCode, bucket: str) -> bool:
    """Check quota availability for generate/export bucket."""
    if bucket == 'generate':
        limit = code_obj.max_generate_requests
        used = code_obj.used_generate_requests or 0
    elif bucket == 'export':
        limit = code_obj.max_export_requests
        used = code_obj.used_export_requests or 0
    else:
        return True
    if limit is None:
        return True
    return used < limit


def get_remaining_quota(code_obj: AccessCode) -> dict:
    """Get remaining quota snapshot for frontend display."""

    def _remaining(limit: Optional[int], used: Optional[int]) -> Optional[int]:
        if limit is None:
            return None
        return max(limit - (used or 0), 0)

    return {
        'generate': _remaining(code_obj.max_generate_requests, code_obj.used_generate_requests),
        'export': _remaining(code_obj.max_export_requests, code_obj.used_export_requests),
    }


def increment_usage(code_id: int, bucket: str) -> None:
    """Increment usage counter after successful request."""
    try:
        if bucket == 'generate':
            db.session.query(AccessCode).filter(AccessCode.id == code_id).update(
                {
                    AccessCode.used_generate_requests: AccessCode.used_generate_requests + 1,
                    AccessCode.updated_at: datetime.utcnow(),
                },
                synchronize_session=False,
            )
        elif bucket == 'export':
            db.session.query(AccessCode).filter(AccessCode.id == code_id).update(
                {
                    AccessCode.used_export_requests: AccessCode.used_export_requests + 1,
                    AccessCode.updated_at: datetime.utcnow(),
                },
                synchronize_session=False,
            )
        else:
            return
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        logger.warning("Failed to increment access code usage: %s", exc)


def classify_quota_bucket(path: str, method: str) -> Optional[str]:
    """Classify endpoint into quota buckets with minimal rules."""
    request_path = (path or '').lower()
    if '/export/' in request_path:
        return 'export'
    if (method or '').upper() != 'POST':
        return None
    if (
        '/generate/' in request_path
        or request_path.endswith('/materials/generate')
        or request_path.endswith('/materials/process')
    ):
        return 'generate'
    return None


def _to_int_or_none(value) -> Optional[int]:
    if value is None or value == '':
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _to_bool(value, default: bool = True) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        text = value.strip().lower()
        if text in ('1', 'true', 'yes', 'y', 'on'):
            return True
        if text in ('0', 'false', 'no', 'n', 'off'):
            return False
    return bool(value)


def sync_codes_from_env() -> int:
    """Sync access codes from ACCESS_CODES_JSON environment variable."""
    import os

    raw = (os.getenv('ACCESS_CODES_JSON') or '').strip()
    if not raw:
        return 0

    try:
        items = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("ACCESS_CODES_JSON is invalid JSON, skip sync")
        return 0

    if not isinstance(items, list):
        logger.warning("ACCESS_CODES_JSON must be a JSON array, skip sync")
        return 0

    upserted = 0
    try:
        for item in items:
            if not isinstance(item, dict):
                continue

            code = str(item.get('code', '')).strip()
            if not code:
                continue

            code_hash = hash_code(code)
            code_obj = AccessCode.query.filter_by(code_hash=code_hash).first()
            if not code_obj:
                code_obj = AccessCode(code_hash=code_hash)
                db.session.add(code_obj)

            code_obj.plan_name = item.get('plan_name')
            code_obj.is_active = _to_bool(item.get('is_active'), default=True)
            code_obj.expires_at = _parse_expire_time(item.get('expires_at'))
            code_obj.max_generate_requests = _to_int_or_none(item.get('max_generate_requests'))
            code_obj.max_export_requests = _to_int_or_none(item.get('max_export_requests'))
            upserted += 1

        if upserted:
            db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        logger.warning("Failed to sync ACCESS_CODES_JSON: %s", exc)
        return 0

    return upserted
