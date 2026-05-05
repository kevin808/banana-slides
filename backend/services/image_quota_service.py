"""
Image generation quota helpers.
"""
from __future__ import annotations

from typing import Any

from flask import current_app

from models import Task

IMAGE_QUOTA_TASK_TYPES = (
    'GENERATE_IMAGES',
    'GENERATE_PAGE_IMAGE',
    'EDIT_PAGE_IMAGE',
    'GENERATE_MATERIAL',
    'PROCESS_MATERIAL',
)


def _safe_progress_int(progress: dict[str, Any], key: str, default: int) -> int:
    value = progress.get(key, default)
    try:
        return max(int(value), 0)
    except (TypeError, ValueError):
        return default


def get_image_generation_limit() -> int | None:
    """
    Return the configured image generation cap.

    None means unlimited.
    """
    raw_value = current_app.config.get('MAX_FREE_GENERATED_IMAGES', 1000)
    try:
        limit = int(raw_value)
    except (TypeError, ValueError):
        limit = 1000
    return None if limit <= 0 else limit


def get_image_generation_usage_snapshot() -> dict[str, int | None]:
    """
    Calculate completed usage plus reserved in-flight image generation slots.
    """
    limit = get_image_generation_limit()
    completed = 0
    reserved = 0

    tasks = Task.query.filter(Task.task_type.in_(IMAGE_QUOTA_TASK_TYPES)).all()
    for task in tasks:
        progress = task.get_progress()
        total = _safe_progress_int(progress, 'total', 1)
        completed_count = _safe_progress_int(progress, 'completed', 0)
        failed_count = _safe_progress_int(progress, 'failed', 0)

        if task.status == 'COMPLETED':
            completed += completed_count
        elif task.status in ('PENDING', 'PROCESSING'):
            reserved += max(total - completed_count - failed_count, 0)

    used = completed + reserved
    remaining = None if limit is None else max(limit - used, 0)

    return {
        'limit': limit,
        'completed': completed,
        'reserved': reserved,
        'used': used,
        'remaining': remaining,
    }


def check_image_generation_quota(requested_count: int) -> tuple[bool, dict[str, int | None]]:
    """
    Validate whether the requested number of images can still be generated.
    """
    snapshot = get_image_generation_usage_snapshot()
    limit = snapshot['limit']
    if limit is None:
        return True, snapshot
    remaining = snapshot['remaining'] or 0
    return remaining >= requested_count, snapshot


def build_image_generation_quota_message(requested_count: int, snapshot: dict[str, int | None]) -> str:
    limit = snapshot['limit']
    remaining = snapshot['remaining']
    used = snapshot['used']
    return (
        f"免费图片额度已达上限：最多 {limit} 张，当前已使用或预留 {used} 张，"
        f"剩余 {remaining} 张，不足以继续生成 {requested_count} 张图片。"
    )
