from datetime import date, datetime, timedelta, timezone
from app import db

class Subscription(db.Model):
    __tablename__ = 'subscriptions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    company_name = db.Column(db.String(255), nullable=False)
    subscription_name = db.Column(db.String(255), nullable=False)
    account = db.Column(db.String(255), nullable=False)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    is_sponsored = db.Column(db.Boolean, nullable=False, default=False)
    sponsor_company = db.Column(db.String(255), nullable=True)
    sponsor_account = db.Column(db.String(255), nullable=True)
    note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    user = db.relationship('User', backref=db.backref('subscriptions', cascade='all, delete-orphan', lazy=True))

    @property
    def days_until_expiry(self):
        """
        Calculates number of days until expiry relative to present date (today).
        Returns negative integer for expired, 0 for expiring today, positive for future, None for no expiry.
        """
        if self.end_date is None:
            return None
        return (self.end_date - date.today()).days

    @property
    def expiry_info(self) -> str:
        """
        Returns a user-friendly string describing the status relative to present date.
        """
        if self.end_date is None:
            return "No expiry date"
        days = self.days_until_expiry
        if days < 0:
            abs_days = abs(days)
            return f"Expired {abs_days} day{'s' if abs_days != 1 else ''} ago"
        elif days == 0:
            return "Expires today"
        elif days == 1:
            return "Expires tomorrow"
        elif days <= 30:
            return f"Expires in {days} days"
        else:
            return f"Expires in {days} days"

    @property
    def status(self) -> str:
        """
        Calculates status dynamically based on current local date (today), start_date, and end_date:
        - No Expiry: end_date is None
        - Expired: end_date is before today
        - Expiring Soon: end_date is today or within the next 30 days (and subscription has started)
        - Active: end_date is more than 30 days away (or start_date is in the future)
        """
        if self.end_date is None:
            return "No Expiry"

        today = date.today()
        if self.end_date < today:
            return "Expired"
        elif self.start_date and self.start_date > today:
            # Subscription start_date is in the future relative to present date
            return "Active"
        elif today <= self.end_date <= (today + timedelta(days=30)):
            return "Expiring Soon"
        else:
            return "Active"

    def to_dict(self):
        return {
            "id": self.id,
            "company_name": self.company_name,
            "subscription_name": self.subscription_name,
            "account": self.account,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "is_sponsored": self.is_sponsored,
            "sponsor_company": self.sponsor_company,
            "sponsor_account": self.sponsor_account,
            "note": self.note,
            "status": self.status,
            "days_until_expiry": self.days_until_expiry,
            "expiry_info": self.expiry_info,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<Subscription {self.company_name} - {self.subscription_name}>'
