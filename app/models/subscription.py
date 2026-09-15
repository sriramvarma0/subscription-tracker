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
    end_date = db.Column(db.Date, nullable=False)
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
    def status(self) -> str:
        """
        Calculates status dynamically based on current local date and end_date:
        - No Expiry: end_date is None
        - Expired: end_date is before today
        - Expiring Soon: end_date is today or within the next 30 days
        - Active: end_date is more than 30 days away
        """
        if self.end_date is None:
            return "No Expiry"

        today = date.today()
        if self.end_date < today:
            return "Expired"
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
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<Subscription {self.company_name} - {self.subscription_name}>'
