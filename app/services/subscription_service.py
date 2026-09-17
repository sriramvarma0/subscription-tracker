from datetime import date, datetime
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy import or_, func
from app import db
from app.models.subscription import Subscription
from app.models.renewal import SubscriptionRenewal
from app.utils import get_user_today

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
        auto_renew_raw = (data.get('auto_renew') or 'NO').strip().upper()
        is_sponsored_raw = data.get('is_sponsored')
        sponsor_company = (data.get('sponsor_company') or '').strip()
        sponsor_account = (data.get('sponsor_account') or '').strip()
        note = (data.get('note') or '').strip()
        no_expiry_raw = data.get('no_expiry') or (data.get('expiry_option') == 'no_expiry')
        if isinstance(no_expiry_raw, str):
            no_expiry = no_expiry_raw.lower() in ('true', 'yes', '1', 'on', 'no_expiry')
        else:
            no_expiry = bool(no_expiry_raw)

        cost_raw = data.get('cost')

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

        # Parse end_date (Compulsory unless No Expiry is selected)
        end_date = None
        if no_expiry:
            end_date = None
        else:
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

            if end_date is None:
                raise ValueError("End date is required unless 'No Expiry' is selected.")

        if start_date and end_date and end_date < start_date:
            raise ValueError("End date cannot be before start date.")

        # Parse auto_renew (YES or NO)
        if auto_renew_raw in ('YES', 'TRUE', '1', 'ON'):
            auto_renew = 'YES'
        else:
            auto_renew = 'NO'

        # Parse is_sponsored
        if isinstance(is_sponsored_raw, str):
            is_sponsored = is_sponsored_raw.lower() in ('true', 'yes', '1', 'on')
        else:
            is_sponsored = bool(is_sponsored_raw)

        currency_raw = (data.get('currency') or 'USD').strip().upper()

        cost = None
        currency = currency_raw if currency_raw else 'USD'

        if is_sponsored:
            if not sponsor_company:
                raise ValueError("Sponsor company is required when subscription is sponsored.")
            sponsor_account = sponsor_account if sponsor_account else None
        else:
            sponsor_company = None
            sponsor_account = None
            if cost_raw is None or str(cost_raw).strip() == '':
                raise ValueError("Subscription cost is required.")
            try:
                cost = float(cost_raw)
            except (ValueError, TypeError):
                raise ValueError("Cost must be a valid number.")
            if cost < 0:
                raise ValueError("Cost cannot be negative.")

        return {
            'company_name': company_name,
            'subscription_name': subscription_name,
            'account': account,
            'start_date': start_date,
            'end_date': end_date,
            'cost': cost,
            'currency': currency,
            'auto_renew': auto_renew,
            'is_sponsored': is_sponsored,
            'sponsor_company': sponsor_company,
            'sponsor_account': sponsor_account,
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

        # Apply sorting relative to present date (today in user timezone)
        today = get_user_today()
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
    def renew_subscription(user_id: int, subscription_id: int, data: Dict[str, Any], default_renewal_type: str = 'MANUAL') -> Subscription:
        subscription = SubscriptionService.get_user_subscription(user_id, subscription_id)
        if not subscription:
            raise KeyError("Subscription not found or access denied.")

        new_start_date_raw = data.get('new_start_date') or data.get('start_date')
        new_end_date_raw = data.get('new_end_date') or data.get('end_date')
        renewal_type_raw = (data.get('renewal_type') or default_renewal_type).strip().upper()
        renewal_type = 'AUTO' if renewal_type_raw == 'AUTO' else 'MANUAL'
        renewal_note = (data.get('renewal_note') or data.get('note') or '').strip()

        # Parse new_start_date (Required)
        if isinstance(new_start_date_raw, str):
            new_start_date_raw = new_start_date_raw.strip()
            if not new_start_date_raw:
                raise ValueError("New start date is required.")
            try:
                new_start_date = datetime.strptime(new_start_date_raw, '%Y-%m-%d').date()
            except ValueError:
                raise ValueError("New start date must be in YYYY-MM-DD format.")
        elif isinstance(new_start_date_raw, date):
            new_start_date = new_start_date_raw
        else:
            raise ValueError("New start date is required.")

        # Parse new_end_date (Required)
        if isinstance(new_end_date_raw, str):
            new_end_date_raw = new_end_date_raw.strip()
            if not new_end_date_raw:
                raise ValueError("New end date is required for renewal.")
            try:
                new_end_date = datetime.strptime(new_end_date_raw, '%Y-%m-%d').date()
            except ValueError:
                raise ValueError("New end date must be in YYYY-MM-DD format.")
        elif isinstance(new_end_date_raw, date):
            new_end_date = new_end_date_raw
        else:
            raise ValueError("New end date is required for renewal.")

        if new_end_date < new_start_date:
            raise ValueError("New end date cannot be before new start date.")

        # Parse auto_renew (If provided, update subscription auto_renew state; otherwise retain existing)
        auto_renew_raw = data.get('auto_renew')
        if auto_renew_raw:
            auto_renew_raw = str(auto_renew_raw).strip().upper()
            if auto_renew_raw in ('YES', 'TRUE', '1', 'ON'):
                subscription.auto_renew = 'YES'
            else:
                subscription.auto_renew = 'NO'

        # Record renewal history
        previous_end_date = subscription.end_date
        renewal = SubscriptionRenewal(
            subscription_id=subscription.id,
            previous_end_date=previous_end_date,
            renewed_on=get_user_today(),
            new_start_date=new_start_date,
            new_end_date=new_end_date,
            renewal_type=renewal_type,
            note=renewal_note if renewal_note else None
        )
        db.session.add(renewal)

        # Update current subscription period
        subscription.start_date = new_start_date
        subscription.end_date = new_end_date

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
