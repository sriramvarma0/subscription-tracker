from datetime import date, datetime
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy import or_, func
from app import db
from app.models.subscription import Subscription

class SubscriptionService:
    @staticmethod
    def validate_and_parse_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates subscription input fields and returns parsed data dictionary.
        Raises ValueError with user-facing message on invalid data.
        """
        company_name = (data.get('company_name') or '').strip()
        subscription_name = (data.get('subscription_name') or '').strip()
        account = (data.get('account') or '').strip()
        start_date_raw = data.get('start_date')
        end_date_raw = data.get('end_date')
        is_sponsored_raw = data.get('is_sponsored')
        sponsor_company = (data.get('sponsor_company') or '').strip()
        sponsor_account = (data.get('sponsor_account') or '').strip()
        note = (data.get('note') or '').strip()

        if not company_name:
            raise ValueError("Company name is required.")
        if not subscription_name:
            raise ValueError("Subscription name is required.")
        if not account:
            raise ValueError("Subscription account is required.")

        # Parse start_date (Optional)
        start_date = None
        if start_date_raw:
            if isinstance(start_date_raw, str):
                start_date_raw = start_date_raw.strip()
                if start_date_raw:
                    try:
                        start_date = datetime.strptime(start_date_raw, '%Y-%m-%d').date()
                    except ValueError:
                        raise ValueError("Start date must be in YYYY-MM-DD format.")
            elif isinstance(start_date_raw, date):
                start_date = start_date_raw

        # Parse end_date (Optional - None indicates No Expiry)
        end_date = None
        if end_date_raw is not None and end_date_raw != '':
            if isinstance(end_date_raw, str):
                end_date_raw = end_date_raw.strip()
                if end_date_raw:
                    try:
                        end_date = datetime.strptime(end_date_raw, '%Y-%m-%d').date()
                    except ValueError:
                        raise ValueError("End date must be in YYYY-MM-DD format.")
            elif isinstance(end_date_raw, date):
                end_date = end_date_raw

        if start_date and end_date and end_date < start_date:
            raise ValueError("End date cannot be before start date.")

        # Parse is_sponsored
        if isinstance(is_sponsored_raw, str):
            is_sponsored = is_sponsored_raw.lower() in ('true', 'yes', '1', 'on')
        else:
            is_sponsored = bool(is_sponsored_raw)

        if is_sponsored:
            if not sponsor_company:
                raise ValueError("Sponsor company is required when subscription is sponsored.")
        else:
            sponsor_company = None
            sponsor_account = None

        return {
            'company_name': company_name,
            'subscription_name': subscription_name,
            'account': account,
            'start_date': start_date,
            'end_date': end_date,
            'is_sponsored': is_sponsored,
            'sponsor_company': sponsor_company if is_sponsored else None,
            'sponsor_account': sponsor_account if (is_sponsored and sponsor_account) else None,
            'note': note if note else None,
        }

    @staticmethod
    def get_subscriptions(
        user_id: int,
        search_query: Optional[str] = None,
        filter_status: Optional[str] = None,
        sort_by: str = 'nearest_expiry'
    ) -> List[Subscription]:
        query = Subscription.query.filter_by(user_id=user_id)

        # Apply search across text fields
        if search_query:
            term = f"%{search_query.strip()}%"
            query = query.filter(
                or_(
                    Subscription.company_name.ilike(term),
                    Subscription.subscription_name.ilike(term),
                    Subscription.account.ilike(term),
                    Subscription.sponsor_company.ilike(term),
                    Subscription.sponsor_account.ilike(term),
                    Subscription.note.ilike(term)
                )
            )

        subscriptions = query.all()

        # Apply status filtering in python because status is dynamically calculated
        if filter_status and filter_status != 'All':
            if filter_status == 'Sponsored':
                subscriptions = [s for s in subscriptions if s.is_sponsored]
            else:
                subscriptions = [s for s in subscriptions if s.status == filter_status]

        # Apply sorting relative to present date (today)
        today = date.today()
        if sort_by == 'farthest_expiry':
            upcoming = [s for s in subscriptions if s.end_date is not None and s.end_date >= today]
            expired = [s for s in subscriptions if s.end_date is not None and s.end_date < today]
            undated = [s for s in subscriptions if s.end_date is None]
            upcoming.sort(key=lambda s: s.end_date, reverse=True)
            expired.sort(key=lambda s: s.end_date, reverse=False)
            subscriptions = upcoming + expired + undated
        elif sort_by == 'company_az':
            subscriptions.sort(key=lambda s: s.company_name.lower())
        elif sort_by == 'recently_added':
            subscriptions.sort(key=lambda s: s.created_at, reverse=True)
        else: # nearest_expiry (default)
            # Upcoming/current sorted ascending by end_date (nearest future expiry first),
            # then expired sorted descending by end_date (most recently expired first),
            # then undated items at the end
            upcoming = [s for s in subscriptions if s.end_date is not None and s.end_date >= today]
            expired = [s for s in subscriptions if s.end_date is not None and s.end_date < today]
            undated = [s for s in subscriptions if s.end_date is None]
            upcoming.sort(key=lambda s: s.end_date)
            expired.sort(key=lambda s: s.end_date, reverse=True)
            subscriptions = upcoming + expired + undated

        return subscriptions

    @staticmethod
    def get_user_summary_counts(user_id: int) -> Dict[str, int]:
        all_subs = Subscription.query.filter_by(user_id=user_id).all()
        counts = {
            'total': len(all_subs),
            'active': 0,
            'expiring_soon': 0,
            'expired': 0,
            'no_expiry': 0
        }
        for sub in all_subs:
            st = sub.status
            if st == 'Active':
                counts['active'] += 1
            elif st == 'Expiring Soon':
                counts['expiring_soon'] += 1
            elif st == 'Expired':
                counts['expired'] += 1
            elif st == 'No Expiry':
                counts['no_expiry'] += 1
        return counts

    @staticmethod
    def create_subscription(user_id: int, data: Dict[str, Any]) -> Subscription:
        parsed = SubscriptionService.validate_and_parse_data(data)
        subscription = Subscription(user_id=user_id, **parsed)
        db.session.add(subscription)
        db.session.commit()
        return subscription

    @staticmethod
    def get_user_subscription(user_id: int, subscription_id: int) -> Optional[Subscription]:
        return Subscription.query.filter_by(id=subscription_id, user_id=user_id).first()

    @staticmethod
    def update_subscription(user_id: int, subscription_id: int, data: Dict[str, Any]) -> Subscription:
        subscription = SubscriptionService.get_user_subscription(user_id, subscription_id)
        if not subscription:
            raise KeyError("Subscription not found or access denied.")

        parsed = SubscriptionService.validate_and_parse_data(data)
        for field, val in parsed.items():
            setattr(subscription, field, val)

        db.session.commit()
        return subscription

    @staticmethod
    def delete_subscription(user_id: int, subscription_id: int) -> bool:
        subscription = SubscriptionService.get_user_subscription(user_id, subscription_id)
        if not subscription:
            raise KeyError("Subscription not found or access denied.")

        db.session.delete(subscription)
        db.session.commit()
        return True
