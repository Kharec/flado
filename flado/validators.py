"""Input validation utilities for Flado."""
import re
from typing import Optional, List, Tuple


def validate_title(title: Optional[str]) -> Tuple[bool, Optional[str]]:
    """
    Validate task title.

    Args:
        title: Title to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not title:
        return False, "Title is required"

    title = title.strip()
    if not title:
        return False, "Title cannot be empty"

    if len(title) > 200:
        return False, "Title must be 200 characters or less"

    return True, None


def validate_description(description: Optional[str]) -> Tuple[bool, Optional[str]]:
    """
    Validate task description.

    Args:
        description: Description to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if description is None:
        return True, None

    description = description.strip()
    if len(description) > 10000:  # Reasonable limit for text field
        return False, "Description must be 10000 characters or less"

    return True, None


def validate_date_format(date_str: Optional[str]) -> Tuple[bool, Optional[str]]:
    """
    Validate date string format (YYYY-MM-DD).

    Args:
        date_str: Date string to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not date_str:
        return True, None

    if not isinstance(date_str, str):
        return False, "Date must be a string"

    # Check format YYYY-MM-DD
    pattern = r'^\d{4}-\d{2}-\d{2}$'
    if not re.match(pattern, date_str):
        return False, "Date must be in YYYY-MM-DD format"

    return True, None


def validate_tag_name(tag_name: Optional[str]) -> Tuple[bool, Optional[str]]:
    """
    Validate tag name.

    Args:
        tag_name: Tag name to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not tag_name:
        return False, "Tag name is required"

    tag_name = tag_name.strip()
    if not tag_name:
        return False, "Tag name cannot be empty"

    if len(tag_name) > 50:
        return False, "Tag name must be 50 characters or less"

    # Allow alphanumeric, spaces, hyphens, underscores
    if not re.match(r'^[\w\s-]+$', tag_name):
        return False, "Tag name contains invalid characters"

    return True, None


def validate_tag_names(tag_names: Optional[List[str]]) -> Tuple[bool, Optional[str]]:
    """
    Validate list of tag names.

    Args:
        tag_names: List of tag names to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if tag_names is None:
        return True, None

    if not isinstance(tag_names, list):
        return False, "Tags must be a list"

    for tag_name in tag_names:
        is_valid, error = validate_tag_name(tag_name)
        if not is_valid:
            return False, error

    return True, None


def validate_hex_color(color: Optional[str]) -> Tuple[bool, Optional[str]]:
    """
    Validate hex color format.

    Args:
        color: Hex color string (e.g., #RRGGBB)

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not color:
        return True, None

    if not isinstance(color, str):
        return False, "Color must be a string"

    pattern = r'^#[0-9A-Fa-f]{6}$'
    if not re.match(pattern, color):
        return False, "Color must be in #RRGGBB hex format"

    return True, None


def validate_task_ids(task_ids: Optional[List[int]]) -> Tuple[bool, Optional[str]]:
    """
    Validate list of task IDs.

    Args:
        task_ids: List of task IDs to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not task_ids:
        return False, "task_ids is required"

    if not isinstance(task_ids, list):
        return False, "task_ids must be a list"

    if len(task_ids) == 0:
        return False, "task_ids cannot be empty"

    for task_id in task_ids:
        if not isinstance(task_id, int):
            return False, "All task IDs must be integers"
        if task_id <= 0:
            return False, "All task IDs must be positive integers"

    return True, None
