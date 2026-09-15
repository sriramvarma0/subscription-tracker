import re
from datetime import datetime, timezone
from app import db

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    @staticmethod
    def normalize_email(email: str) -> str:
        if not email:
            return ""
        return email.strip().lower()

    @staticmethod
    def validate_email(email: str) -> bool:
        normalized = User.normalize_email(email)
        if not normalized:
            return False
        # Basic email format check: local-part@domain.tld
        pattern = r'^[^@\s]+@[^@\s]+\.[^@\s]+$'
        return bool(re.match(pattern, normalized))

    def __repr__(self):
        return f'<User {self.email}>'
