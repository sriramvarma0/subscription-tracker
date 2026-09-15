import pytest
from app import db
from app.services.subscription_service import SubscriptionService
from app.models.subscription import Subscription

def test_multi_user_data_isolation(client, app, user_a, user_b):
    with app.app_context():
        # User A creates a subscription
        sub_a = SubscriptionService.create_subscription(user_a.id, {
            'company_name': 'User A Service',
            'subscription_name': 'Secret Sub',
            'account': 'user_a_acc',
            'end_date': '2026-12-31'
        })
        sub_a_id = sub_a.id

        # User B creates a subscription
        sub_b = SubscriptionService.create_subscription(user_b.id, {
            'company_name': 'User B Service',
            'subscription_name': 'Private Sub',
            'account': 'user_b_acc',
            'end_date': '2026-12-31'
        })
        sub_b_id = sub_b.id

    # 1. User B logs in
    with client.session_transaction() as sess:
        sess['user_id'] = user_b.id

    # User B views dashboard -> must NOT see User A's subscription
    res = client.get('/', follow_redirects=True)
    assert res.status_code == 200
    assert b"User B Service" in res.data
    assert b"User A Service" not in res.data

    # User B tries to fetch User A's subscription via GET -> HTTP 404
    res_get = client.get(f'/subscriptions/{sub_a_id}')
    assert res_get.status_code == 404

    # User B tries to edit User A's subscription -> HTTP 404 / error
    res_edit = client.post(f'/subscriptions/{sub_a_id}/edit', data={
        'company_name': 'Hacked Company',
        'subscription_name': 'Hacked Sub',
        'account': 'hacked_acc',
        'end_date': '2026-12-31'
    }, follow_redirects=True)
    assert b"Subscription not found or access denied." in res_edit.data

    with app.app_context():
        sub_a_db = db.session.get(Subscription, sub_a_id)
        assert sub_a_db.company_name == 'User A Service'

    # User B tries to delete User A's subscription -> HTTP 404 / error
    res_del = client.post(f'/subscriptions/{sub_a_id}/delete', follow_redirects=True)
    assert b"Subscription not found or access denied." in res_del.data

    with app.app_context():
        assert db.session.get(Subscription, sub_a_id) is not None

    # User B exports CSV -> must only contain User B data
    res_csv = client.get('/export/csv')
    assert res_csv.status_code == 200
    assert b"User B Service" in res_csv.data
    assert b"User A Service" not in res_csv.data

    # User B exports JSON -> must only contain User B data
    res_json = client.get('/export/json')
    assert res_json.status_code == 200
    assert b"User B Service" in res_json.data
    assert b"User A Service" not in res_json.data
