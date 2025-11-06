"""Blueprint for task-related routes."""
import logging
from datetime import datetime, date
from typing import Dict, Any, Tuple

from flask import Blueprint, render_template, request, jsonify, Response
from sqlalchemy import text

from .models import Task, db
from .services import (
    get_tasks, create_task, update_task, delete_task,
    reorder_tasks, get_all_tags
)
from .validators import (
    validate_title, validate_description, validate_date_format,
    validate_tag_names, validate_task_ids
)

logger = logging.getLogger(__name__)

tasks_blueprint = Blueprint('tasks', __name__, url_prefix='/')


@tasks_blueprint.route('/health')
def health_check() -> Response:
    """
    Health check endpoint for monitoring.

    Returns:
        JSON response with health status
    """
    try:
        # Test database connection
        db.session.execute(text('SELECT 1'))
        return jsonify({
            'status': 'healthy',
            'database': 'connected'
        }), 200
    except Exception as e:
        logger.error(f'Health check failed: {e}')
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e)
        }), 503


@tasks_blueprint.route('/')
def index() -> str:
    """Render the main task list page."""
    filter_type = request.args.get('filter', 'all')
    search_query = request.args.get('search', '')

    # Validate filter type
    valid_filters = ['all', 'today', 'upcoming', 'active', 'completed']
    if filter_type not in valid_filters:
        filter_type = 'all'

    try:
        tasks = get_tasks(
            filter_type, search_query if search_query else None).all()
        tags = get_all_tags()

        return render_template(
            'index.html',
            tasks=tasks,
            tags=tags,
            filter_type=filter_type,
            search_query=search_query,
            today=date.today()
        )
    except Exception as e:
        logger.error(f'Error rendering index: {e}')
        # Return empty state on error
        return render_template(
            'index.html',
            tasks=[],
            tags=[],
            filter_type=filter_type,
            search_query=search_query,
            today=date.today()
        )


@tasks_blueprint.route('/api/tasks', methods=['POST'])
def api_create_task() -> Tuple[Response, int]:
    """API endpoint to create a new task."""
    try:
        data = request.get_json()
        if not isinstance(data, dict):
            return jsonify({'error': 'Invalid JSON payload'}), 400

        # Validate title
        title = data.get('title')
        is_valid, error = validate_title(title)
        if not is_valid:
            return jsonify({'error': error}), 400
        title = title.strip()

        # Validate description
        description = data.get('description')
        is_valid, error = validate_description(description)
        if not is_valid:
            return jsonify({'error': error}), 400
        description = description.strip() if description else None

        # Validate and parse due date
        due_date_str = data.get('due_date')
        due_date = None
        if due_date_str:
            is_valid, error = validate_date_format(due_date_str)
            if not is_valid:
                return jsonify({'error': error}), 400
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Invalid date value'}), 400

        # Validate tags
        tag_names = data.get('tags', [])
        is_valid, error = validate_tag_names(tag_names)
        if not is_valid:
            return jsonify({'error': error}), 400

        task = create_task(title, description, due_date, tag_names)
        logger.info(f'Created task {task.id}: {task.title}')
        return jsonify(task.to_dict()), 201

    except Exception as e:
        logger.error(f'Error creating task: {e}')
        return jsonify({'error': 'Internal server error'}), 500


@tasks_blueprint.route('/api/tasks/<int:task_id>', methods=['GET'])
def api_get_task(task_id: int) -> Tuple[Response, int]:
    """API endpoint to get a single task."""
    try:
        task = Task.query.get_or_404(task_id)
        return jsonify(task.to_dict())
    except Exception as e:
        logger.error(f'Error fetching task {task_id}: {e}')
        return jsonify({'error': 'Internal server error'}), 500


@tasks_blueprint.route('/api/tasks/<int:task_id>', methods=['PUT', 'PATCH'])
def api_update_task(task_id: int) -> Tuple[Response, int]:
    """API endpoint to update a task."""
    try:
        data = request.get_json()
        if not isinstance(data, dict):
            return jsonify({'error': 'Invalid JSON payload'}), 400

        update_data: Dict[str, Any] = {}

        # Validate and update title
        if 'title' in data:
            is_valid, error = validate_title(data['title'])
            if not is_valid:
                return jsonify({'error': error}), 400
            update_data['title'] = data['title'].strip()

        # Validate and update description
        if 'description' in data:
            is_valid, error = validate_description(data['description'])
            if not is_valid:
                return jsonify({'error': error}), 400
            description = data['description']
            update_data['description'] = description.strip(
            ) if description else None

        # Validate and update completed status
        if 'completed' in data:
            if not isinstance(data['completed'], bool):
                return jsonify({'error': 'completed must be a boolean'}), 400
            update_data['completed'] = data['completed']

        # Validate and update due date
        if 'due_date' in data:
            due_date_str = data['due_date']
            if due_date_str:
                is_valid, error = validate_date_format(due_date_str)
                if not is_valid:
                    return jsonify({'error': error}), 400
                try:
                    update_data['due_date'] = datetime.strptime(
                        due_date_str, '%Y-%m-%d').date()
                except ValueError:
                    return jsonify({'error': 'Invalid date value'}), 400
            else:
                update_data['due_date'] = None

        # Validate and update tags
        if 'tags' in data:
            tag_names = data['tags']
            is_valid, error = validate_tag_names(tag_names)
            if not is_valid:
                return jsonify({'error': error}), 400
            update_data['tag_names'] = tag_names

        task = update_task(task_id, **update_data)
        logger.info(f'Updated task {task_id}')
        return jsonify(task.to_dict())

    except Exception as e:
        logger.error(f'Error updating task {task_id}: {e}')
        return jsonify({'error': 'Internal server error'}), 500


@tasks_blueprint.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def api_delete_task(task_id: int) -> Tuple[Response, int]:
    """API endpoint to delete a task."""
    try:
        delete_task(task_id)
        logger.info(f'Deleted task {task_id}')
        return jsonify({'success': True}), 200
    except Exception as e:
        logger.error(f'Error deleting task {task_id}: {e}')
        return jsonify({'error': 'Internal server error'}), 500


@tasks_blueprint.route('/api/tasks/reorder', methods=['POST'])
def api_reorder_tasks() -> Tuple[Response, int]:
    """API endpoint to reorder tasks."""
    try:
        data = request.get_json()
        if not isinstance(data, dict):
            return jsonify({'error': 'Invalid JSON payload'}), 400

        task_ids = data.get('task_ids', [])

        # Validate task IDs
        is_valid, error = validate_task_ids(task_ids)
        if not is_valid:
            return jsonify({'error': error}), 400

        reorder_tasks(task_ids)
        logger.info(f'Reordered {len(task_ids)} tasks')
        return jsonify({'success': True}), 200

    except Exception as e:
        logger.error(f'Error reordering tasks: {e}')
        return jsonify({'error': 'Internal server error'}), 500
