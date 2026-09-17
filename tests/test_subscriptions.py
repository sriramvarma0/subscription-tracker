from datetime import date, timedelta
import pytest
from app import db
from app.models.subscription import Subscription
from app.services.subscription_service import SubscriptionService

def test_status_calculation(app, user_a):
    today = date.today()
    with app.app_context():
        # No Expiry
        sub1 = Subscription(
            user_id=user_a.id, company_name="Netflix", subscription_name="Standard",
            account="user@gmail.com", start_date=today, end_date=None
        )
        assert sub1.status == "No Expiry"
        assert sub1.days_until_expiry is None
        assert sub1.expiry_info == "No expiry date"

        # Expired
        sub2 = Subscription(
            user_id=user_a.id, company_name="Gym", subscription_name="Annual Pass",
            account="Pass123", start_date=today - timedelta(days=100), end_date=today - timedelta(days=10)
        )
        assert sub2.status == "Expired"
        assert sub2.days_until_expiry == -10
        assert sub2.expiry_info == "Expired 10 days ago"

        # Expiring Soon
        sub3 = Subscription(
            user_id=user_a.id, company_name="Domain Registrar", subscription_name=".com renewal",
            account="my-domain.com", start_date=today - timedelta(days=300), end_date=today + timedelta(days=15)
        )
        assert sub3.status == "Expiring Soon"
        assert sub3.days_until_expiry == 15
        assert sub3.expiry_info == "Expires in 15 days"

        # Active
        sub4 = Subscription(
            user_id=user_a.id, company_name="Cloud Hosting", subscription_name="VPS Plan",
            account="AWS-123", start_date=today, end_date=today + timedelta(days=60)
        )
        assert sub4.status == "Active"
        assert sub4.days_until_expiry == 60
        assert sub4.expiry_info == "Expires in 60 days"

        # Future Start Date (Upcoming)
        sub5 = Subscription(
            user_id=user_a.id, company_name="Conference Pass", subscription_name="Ticket",
            account="Event123", start_date=today + timedelta(days=10), end_date=today + timedelta(days=20)
        )
        assert sub5.status == "Active"

def test_create_subscription_validation(app, user_a):
    today = date.today()
    with app.app_context():
        # Missing required field company_name
        with pytest.raises(ValueError, match="Company name is required"):
            SubscriptionService.create_subscription(user_a.id, {
                'company_name': '', 'subscription_name': 'Plan', 'account': 'acc', 'start_date': '2026-01-01', 'end_date': '2026-12-31'
            })

        # Missing cost for non-sponsored subscription
        with pytest.raises(ValueError, match="Subscription cost is required"):
            SubscriptionService.create_subscription(user_a.id, {
                'company_name': 'Co', 'subscription_name': 'Plan', 'account': 'acc', 'end_date': (today + timedelta(days=60)).isoformat()
            })

        # Omitted start_date stays None (optional)
        sub_default_start = SubscriptionService.create_subscription(user_a.id, {
            'company_name': 'Company', 'subscription_name': 'Plan', 'account': 'acc', 'end_date': (today + timedelta(days=60)).isoformat(), 'cost': '10.00'
        })
        assert sub_default_start.start_date is None
        assert sub_default_start.cost == 10.00

        # End date missing without No Expiry
        with pytest.raises(ValueError, match="End date is required unless 'No Expiry' is selected"):
            SubscriptionService.create_subscription(user_a.id, {
                'company_name': 'Co', 'subscription_name': 'Plan', 'account': 'acc', 'start_date': today.isoformat(), 'cost': '10.00'
            })

        # End date before start date
        with pytest.raises(ValueError, match="End date cannot be before start date"):
            SubscriptionService.create_subscription(user_a.id, {
                'company_name': 'Co', 'subscription_name': 'Plan', 'account': 'acc',
                'start_date': (today + timedelta(days=30)).isoformat(),
                'end_date': today.isoformat(),
                'cost': '10.00'
            })

        # Sponsored true without sponsor_company
        with pytest.raises(ValueError, match="Sponsor company is required"):
            SubscriptionService.create_subscription(user_a.id, {
                'company_name': 'Co', 'subscription_name': 'Plan', 'account': 'acc',
                'start_date': today.isoformat(), 'end_date': '2026-12-31', 'is_sponsored': True, 'sponsor_company': ''
            })

        # Negative cost raises error
        with pytest.raises(ValueError, match="Cost cannot be negative"):
            SubscriptionService.create_subscription(user_a.id, {
                'company_name': 'Co', 'subscription_name': 'Plan', 'account': 'acc',
                'end_date': '2026-12-31', 'cost': '-10.50'
            })

        # Optional end_date with no_expiry option
        sub_no_end = SubscriptionService.create_subscription(user_a.id, {
            'company_name': 'No Expiry Sub', 'subscription_name': 'Plan', 'account': 'acc',
            'start_date': today.isoformat(), 'no_expiry': True, 'auto_renew': 'YES', 'cost': '15.99'
        })
        assert sub_no_end.start_date == today
        assert sub_no_end.end_date is None
        assert sub_no_end.cost == 15.99
        assert sub_no_end.auto_renew == 'YES'
        assert sub_no_end.status == "No Expiry"

def test_renewal_workflow(app, client, user_a):
    today = date.today()
    with app.app_context():
        # Create an expired subscription with auto_renew YES
        sub = SubscriptionService.create_subscription(user_a.id, {
            'company_name': 'Google',
            'subscription_name': 'Google One Storage',
            'account': 'sriram@gmail.com',
            'start_date': (today - timedelta(days=365)).isoformat(),
            'end_date': (today - timedelta(days=1)).isoformat(),
            'auto_renew': 'YES',
            'is_sponsored': True,
            'sponsor_company': 'Jio',
            'sponsor_account': 'My first Jio number',
            'note': 'Jio of my first number gave this subscription.'
        })
        assert sub.status == 'Expired'
        assert sub.auto_renew == 'YES'
        assert sub.renewal_count == 0

        # Perform Auto-Renew confirmation
        renewed_sub = SubscriptionService.renew_subscription(user_a.id, sub.id, {
            'new_start_date': today.isoformat(),
            'new_end_date': (today + timedelta(days=365)).isoformat(),
            'renewal_type': 'AUTO',
            'auto_renew': 'YES',
            'renewal_note': 'Confirmed auto-renewal for year 2'
        }, default_renewal_type='AUTO')

        assert renewed_sub.start_date == today
        assert renewed_sub.end_date == today + timedelta(days=365)
        assert renewed_sub.status == 'Active'
        assert renewed_sub.renewal_count == 1
        ren = renewed_sub.renewals[0]
        assert ren.renewal_type == 'AUTO'
        assert ren.previous_end_date == today - timedelta(days=1)
        assert ren.new_start_date == today
        assert ren.new_end_date == today + timedelta(days=365)

        # Perform Manual Renewal
        manual_sub = SubscriptionService.renew_subscription(user_a.id, sub.id, {
            'new_start_date': (today + timedelta(days=366)).isoformat(),
            'new_end_date': (today + timedelta(days=730)).isoformat(),
            'renewal_type': 'MANUAL',
            'auto_renew': 'NO',
            'renewal_note': 'Manual renewal for year 3'
        })
        assert manual_sub.renewal_count == 2
        assert manual_sub.auto_renew == 'NO'
        ren2 = manual_sub.renewals[0] # Order desc by created_at
        assert ren2.renewal_type == 'MANUAL'

def test_subscription_crud(client, app, user_a):
    with client.session_transaction() as sess:
        sess['user_id'] = user_a.id

    # Create via POST
    res = client.post('/subscriptions', data={
        'company_name': 'Spotify',
        'subscription_name': 'Duo Plan',
        'account': 'spotify_user',
        'start_date': '2026-01-01',
        'end_date': '2026-12-31',
        'cost': '14.99',
        'currency': 'USD',
        'auto_renew': 'YES',
        'is_sponsored': 'false',
        'note': 'Shared account'
    }, follow_redirects=True)
    assert res.status_code == 200

    with app.app_context():
        sub = Subscription.query.filter_by(user_id=user_a.id, company_name='Spotify').first()
        assert sub is not None
        sub_id = sub.id
        assert sub.subscription_name == 'Duo Plan'
        assert sub.cost == 14.99
        assert sub.currency == 'USD'
        assert sub.auto_renew == 'YES'
        assert sub.note == 'Shared account'

    # Edit via POST
    res = client.post(f'/subscriptions/{sub_id}/edit', data={
        'company_name': 'Spotify Premium',
        'subscription_name': 'Family Plan',
        'account': 'spotify_user',
        'start_date': '2026-01-01',
        'end_date': '2027-12-31',
        'auto_renew': 'NO',
        'is_sponsored': 'true',
        'sponsor_company': 'Acme Corp',
        'note': 'Upgraded to Family'
    }, follow_redirects=True)
    assert res.status_code == 200

    with app.app_context():
        updated_sub = db.session.get(Subscription, sub_id)
        assert updated_sub.company_name == 'Spotify Premium'
        assert updated_sub.subscription_name == 'Family Plan'
        assert updated_sub.auto_renew == 'NO'
        assert updated_sub.is_sponsored is True
        assert updated_sub.sponsor_company == 'Acme Corp'

    # Delete via POST
    res = client.post(f'/subscriptions/{sub_id}/delete', follow_redirects=True)
    assert res.status_code == 200

    with app.app_context():
        assert db.session.get(Subscription, sub_id) is None

def test_search_filter_sort(app, user_a):
    today = date.today()
    with app.app_context():
        s1 = SubscriptionService.create_subscription(user_a.id, {
            'company_name': 'Adobe Creative Cloud', 'subscription_name': 'All Apps',
            'account': 'design@company.com', 'start_date': '2025-01-01', 'end_date': (today + timedelta(days=10)).isoformat(),
            'cost': '52.99', 'currency': 'USD'
        })
        s2 = SubscriptionService.create_subscription(user_a.id, {
            'company_name': 'GitHub', 'subscription_name': 'Pro',
            'account': 'octocat', 'start_date': '2025-01-01', 'end_date': (today + timedelta(days=90)).isoformat(),
            'is_sponsored': True, 'sponsor_company': 'OpenSourceOrg'
        })
        s3 = SubscriptionService.create_subscription(user_a.id, {
            'company_name': 'Zendesk', 'subscription_name': 'Support',
            'account': 'help@work.com', 'start_date': '2025-01-01', 'end_date': (today - timedelta(days=5)).isoformat(),
            'cost': '19.00', 'currency': 'USD'
        })

        # Search for 'octocat'
        res = SubscriptionService.get_subscriptions(user_a.id, search_query='octocat')
        assert len(res) == 1
        assert res[0].company_name == 'GitHub'

        # Filter by Sponsored
        res_sponsored = SubscriptionService.get_subscriptions(user_a.id, filter_status='Sponsored')
        assert len(res_sponsored) == 1
        assert res_sponsored[0].company_name == 'GitHub'

        # Sort by Nearest Expiry (Adobe in 10 days, GitHub in 90 days, Zendesk expired 5 days ago)
        res_nearest = SubscriptionService.get_subscriptions(user_a.id, sort_by='nearest_expiry')
        assert [s.company_name for s in res_nearest] == ['Adobe Creative Cloud', 'GitHub', 'Zendesk']

        # Sort by Company A-Z
        res_az = SubscriptionService.get_subscriptions(user_a.id, sort_by='company_az')
        assert [s.company_name for s in res_az] == ['Adobe Creative Cloud', 'GitHub', 'Zendesk']
