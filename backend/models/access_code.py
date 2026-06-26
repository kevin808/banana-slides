"""Access code model for SaaS membership quota control."""
from datetime import datetime

from . import db


class AccessCode(db.Model):
    """Membership access code with optional quotas."""

    __tablename__ = 'access_codes'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code_hash = db.Column(db.String(64), nullable=False, unique=True, index=True)
    plan_name = db.Column(db.String(50), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    expires_at = db.Column(db.DateTime, nullable=True)
    max_generate_requests = db.Column(db.Integer, nullable=True)
    max_export_requests = db.Column(db.Integer, nullable=True)
    used_generate_requests = db.Column(db.Integer, nullable=False, default=0)
    used_export_requests = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<AccessCode id={self.id} plan={self.plan_name}>'
