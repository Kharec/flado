"""Business logic helpers for Flado."""
import logging
from datetime import datetime, date, timezone

from sqlalchemy import or_, func
from sqlalchemy.orm import Query

from .models import db, Task, Tag

logger = logging.getLogger(__name__)


def get_tasks(filter_type: str = 'all', search_query: str | None = None) -> Query:
    """
    Retrieve tasks based on filter type.

    Args:
        filter_type: 'all', 'today', 'upcoming', 'completed', 'active'
        search_query: str | None search string to filter by title/description

    Returns:
        Query object of tasks
    """
    query = Task.query

    if filter_type == 'today':
        query = query.filter(Task.due_date == date.today())
    elif filter_type == 'upcoming':
        query = query.filter(Task.due_date > date.today())
    elif filter_type == 'overdue':
        query = query.filter(Task.due_date < date.today(), Task.completed.is_(False))
    elif filter_type == 'completed':
        query = query.filter(Task.completed.is_(True))
    elif filter_type == 'active':
        query = query.filter(Task.completed.is_(False))

    if search_query:
        search_term = f'%{search_query}%'
        query = query.filter(
            or_(
                Task.title.ilike(search_term),
                Task.description.ilike(search_term)
            )
        )

    return query.order_by(Task.position.asc(), Task.created_at.desc())


def create_task(
    title: str,
    description: str | None = None,
    due_date: date | None = None,
    tag_names: list[str] | None = None
) -> Task:
    """
    Create a new task.

    Args:
        title: Task title (required, already validated)
        description: str | None task description (already validated)
        due_date: date | None due date (date object, already validated)
        tag_names: list[str] | None list of tag names to associate (already validated)

    Returns:
        Created Task object

    Raises:
        ValueError: If title is empty or invalid
    """
    if not title or not title.strip():
        raise ValueError("Task title is required")

    try:
        # Get max position for ordering
        max_position = db.session.query(func.max(Task.position)).scalar() or 0

        task = Task(
            title=title.strip(),
            description=description.strip() if description else None,
            due_date=due_date,
            position=max_position + 1
        )

        if tag_names:
            tags = get_or_create_tags(tag_names)
            task.tags = tags

        db.session.add(task)
        db.session.commit()
        return task
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error creating task: {e}')
        raise


def update_task(task_id: int, **kwargs) -> Task:
    """
    Update an existing task.

    Args:
        task_id: ID of task to update
        **kwargs: Fields to update (title, description, completed, due_date, tag_names)

    Returns:
        Updated Task object

    Raises:
        404: If task not found
    """
    task = Task.query.get_or_404(task_id)

    try:
        if 'title' in kwargs and kwargs['title']:
            task.title = kwargs['title'].strip()
        if 'description' in kwargs:
            task.description = kwargs['description'].strip(
            ) if kwargs['description'] else None
        if 'completed' in kwargs:
            task.completed = kwargs['completed']
        if 'due_date' in kwargs:
            task.due_date = kwargs['due_date']
        if 'tag_names' in kwargs:
            tag_names = kwargs['tag_names']
            if tag_names:
                tags = get_or_create_tags(tag_names)
                task.tags = tags
            else:
                task.tags = []

        task.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        return task
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error updating task {task_id}: {e}')
        raise


def delete_task(task_id: int) -> bool:
    """
    Delete a task.

    Args:
        task_id: ID of task to delete

    Returns:
        True if deleted successfully

    Raises:
        404: If task not found
    """
    task = Task.query.get_or_404(task_id)
    try:
        db.session.delete(task)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error deleting task {task_id}: {e}')
        raise


def reorder_tasks(task_ids: list[int]) -> bool:
    """
    Reorder tasks by updating their positions.

    Args:
        task_ids: list[int] of task IDs in desired order (already validated)

    Returns:
        True if reordered successfully

    Note:
        Invalid task IDs are silently skipped (task not found).
    """
    try:
        # Fetch all tasks in current order so unaffected tasks keep stable positions
        all_tasks = Task.query.order_by(
            Task.position.asc(), Task.created_at.desc()
        ).all()
        if not all_tasks:
            return True

        id_to_task = {task.id: task for task in all_tasks}

        # Build new ordered list: first the provided IDs (if they exist), then the rest
        reordered_tasks = []
        seen_ids = set()
        for task_id in task_ids:
            task = id_to_task.get(task_id)
            if task and task_id not in seen_ids:
                reordered_tasks.append(task)
                seen_ids.add(task_id)

        for task in all_tasks:
            if task.id not in seen_ids:
                reordered_tasks.append(task)

        for index, task in enumerate(reordered_tasks, start=1):
            task.position = index

        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error reordering tasks: {e}')
        raise


def get_or_create_tags(tag_names: list[str]) -> list[Tag]:
    """
    Get existing tags or create new ones.

    Args:
        tag_names: list[str] of tag names (already validated)

    Returns:
        list[Tag] of tag objects

    Note:
        Does not commit the session. Caller is responsible for committing.
    """
    tags = []
    for tag_name in tag_names:
        tag_name = tag_name.strip()
        if not tag_name:
            continue
        tag = Tag.query.filter_by(name=tag_name).first()
        if not tag:
            tag = Tag(name=tag_name)
            db.session.add(tag)
        tags.append(tag)
    return tags


def get_all_tags() -> list[Tag]:
    """Get all tags."""
    return Tag.query.order_by(Tag.name.asc()).all()
