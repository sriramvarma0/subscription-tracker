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

        # Expired
        sub2 = Subscription(
            user_id=user_a.id, company_name="Gym", subscription_name="Annual Pass",
            account="Pass123", start_date=today - timedelta(days=100), end_date=today - timedelta(days=1)
        )
        assert sub2.status == "Expired"

        # Expiring Soon
        sub3 = Subscription(
            user_id=user_a.id, company_name="Domain Registrar", subscription_name=".com renewal",
            account="my-domain.com", start_date=today - timedelta(days=300), end_date=today + timedelta(days=15)
        )
        assert sub3.status == "Expiring Soon"

        # Active
        sub4 = Subscription(
            user_id=user_a.id, company_name="Cloud Hosting", subscription_name="VPS Plan",
            account="AWS-123", start_date=today, end_date=today + timedelta(days=60)
        )
        assert sub4.status == "Active"

def test_create_subscription_validation(app, user_a):
    today = date.today()
    with app.app_context():
        # Missing required field company_name
        with pytest.raises(ValueError, match="Company name is required"):
            SubscriptionService.create_subscription(user_a.id, {
                'company_name': '', 'subscription_name': 'Plan', 'account': 'acc', 'end_date': '2026-12-31'
            })

        # Missing required field end_date
        with pytest.raises(ValueError, match="End date is required"):
            SubscriptionService.create_subscription(user_a.id, {
                'company_name': 'Company', 'subscription_name': 'Plan', 'account': 'acc', 'start_date': '2026-01-01'
            })

        # End date before start date
        with pytest.raises(ValueError, match="End date cannot be before start date"):
            SubscriptionService.create_subscription(user_a.id, {
                'company_name': 'Co', 'subscription_name': 'Plan', 'account': 'acc',
                'start_date': '2026-05-01', 'end_date': '2026-04-01'
            })

        # Sponsored true without sponsor_company
        with pytest.raises(ValueError, match="Sponsor company is required"):
            SubscriptionService.create_subscription(user_a.id, {
                'company_name': 'Co', 'subscription_name': 'Plan', 'account': 'acc',
                'end_date': '2026-12-31', 'is_sponsored': True, 'sponsor_company': ''
            })

        # Optional start_date (omitted start_date succeeds)
        sub_no_start = SubscriptionService.create_subscription(user_a.id, {
            'company_name': 'Optional Start Co', 'subscription_name': 'Plan', 'account': 'acc',
            'end_date': (today + timedelta(days=60)).isoformat()
        })
        assert sub_no_start.start_date is None
        assert sub_no_start.end_date == today + timedelta(days=60)
        assert sub_no_start.status == "Active"

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
        'is_sponsored': 'false',
        'note': 'Shared account'
    }, follow_redirects=True)
    assert res.status_code == 200

    with app.app_context():
        sub = Subscription.query.filter_by(user_id=user_a.id, company_name='Spotify').first()
        assert sub is not None
        sub_id = sub.id
        assert sub.subscription_name == 'Duo Plan'
        assert sub.note == 'Shared account'

    # Edit via POST
    res = client.post(f'/subscriptions/{sub_id}/edit', data={
        'company_name': 'Spotify Premium',
        'subscription_name': 'Family Plan',
        'account': 'spotify_user',
        'start_date': '2026-01-01',
        'end_date': '2027-12-31',
        'is_sponsored': 'true',
        'sponsor_company': 'Acme Corp',
        'note': 'Upgraded to Family'
    }, follow_redirects=True)
    assert res.status_code == 200

    with app.app_context():
        updated_sub = db.session.get(Subscription, sub_id)
        assert updated_sub.company_name == 'Spotify Premium'
        assert updated_sub.subscription_name == 'Family Plan'
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
            'account': 'design@company.com', 'start_date': '2025-01-01', 'end_date': (today + timedelta(days=10)).isoformat()
        })
        s2 = SubscriptionService.create_subscription(user_a.id, {
            'company_name': 'GitHub', 'subscription_name': 'Pro',
            'account': 'octocat', 'end_date': (today + timedelta(days=90)).isoformat(),
            'is_sponsored': True, 'sponsor_company': 'OpenSourceOrg'
        })
        s3 = SubscriptionService.create_subscription(user_a.id, {
            'company_name': 'Zendesk', 'subscription_name': 'Support',
            'account': 'help@work.com', 'start_date': '2025-01-01', 'end_date': (today - timedelta(days=5)).isoformat()
        })

        # Search for 'octocat'
        res = SubscriptionService.get_subscriptions(user_a.id, search_query='octocat')
        assert len(res) == 1
        assert res[0].company_name == 'GitHub'

        # Filter by Sponsored
        res_sponsored = SubscriptionService.get_subscriptions(user_a.id, filter_status='Sponsored')
        assert len(res_sponsored) == 1
        assert res_sponsored[0].company_name == 'GitHub'

        # Sort by Company A-Z
        res_az = SubscriptionService.get_subscriptions(user_a.id, sort_by='company_az')
        assert [s.company_name for s in res_az] == ['Adobe Creative Cloud', 'GitHub', 'Zendesk']
