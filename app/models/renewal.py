from datetime import datetime, timezone
from app import db
from app.utils import get_user_today

class SubscriptionRenewal(db.Model):
    __tablename__ = 'subscription_renewals'

    id = db.Column(db.Integer, primary_key=True)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscriptions.id', ondelete='CASCADE'), nullable=False, index=True)
    previous_end_date = db.Column(db.Date, nullable=True)
    renewed_on = db.Column(db.Date, default=get_user_today, nullable=False)
    new_start_date = db.Column(db.Date, nullable=False)
    new_end_date = db.Column(db.Date, nullable=False)
    renewal_type = db.Column(db.String(10), nullable=False) # 'AUTO' or 'MANUAL'
    note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "subscription_id": self.subscription_id,
            "previous_end_date": self.previous_end_date.isoformat() if self.previous_end_date else None,
            "renewed_on": self.renewed_on.isoformat() if self.renewed_on else None,
            "new_start_date": self.new_start_date.isoformat() if self.new_start_date else None,
            "new_end_date": self.new_end_date.isoformat() if self.new_end_date else None,
            "renewal_type": self.renewal_type,
            "note": self.note,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<SubscriptionRenewal sub_id={self.subscription_id} type={self.renewal_type} {self.new_start_date}->{self.new_end_date}>'
