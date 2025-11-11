"""SQLAlchemy models for Flado."""
from datetime import datetime, timezone
from typing import Dict, Any

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


class Task(db.Model):
    """Task model representing a todo item."""
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    completed = db.Column(db.Boolean, default=False, nullable=False)
    due_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(
        db.DateTime, default=utc_now, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=utc_now, onupdate=utc_now, nullable=False)
    position = db.Column(db.Integer, default=0, nullable=False)
    tags = db.relationship('Tag', secondary='task_tags',
                           back_populates='tasks', lazy='select')

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'completed': self.completed,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'position': self.position,
            'tags': [tag.name for tag in self.tags]
        }

    def __repr__(self) -> str:
        return f'<Task {self.id}: {self.title}>'


class Tag(db.Model):
    """Tag model for categorizing tasks."""
    __tablename__ = 'tags'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    color = db.Column(db.String(7), default='#3b82f6',
                      nullable=False)  # Hex color
    tasks = db.relationship('Task', secondary='task_tags',
                            back_populates='tags', lazy='dynamic')

    def __repr__(self) -> str:
        return f'<Tag {self.name}>'


# Association table for many-to-many relationship
task_tags = db.Table('task_tags',
                     db.Column('task_id', db.Integer, db.ForeignKey(
                         'tasks.id'), primary_key=True),
                     db.Column('tag_id', db.Integer, db.ForeignKey(
                         'tags.id'), primary_key=True)
                     )
