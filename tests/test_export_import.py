import io
import json
import pytest
from app.services.subscription_service import SubscriptionService
from app.models.subscription import Subscription

def test_csv_export(client, app, user_a):
    with app.app_context():
        SubscriptionService.create_subscription(user_a.id, {
            'company_name': 'Netflix',
            'subscription_name': '4K Plan',
            'account': 'netflix@user.com',
            'end_date': '2026-12-31',
            'note': 'Movie night'
        })

    with client.session_transaction() as sess:
        sess['user_id'] = user_a.id

    res = client.get('/export/csv')
    assert res.status_code == 200
    assert res.mimetype == 'text/csv'
    csv_text = res.data.decode('utf-8')
    assert 'Company Name,Subscription Name' in csv_text
    assert 'Netflix,4K Plan,netflix@user.com' in csv_text

def test_json_export_and_import(client, app, user_a, user_b):
    with app.app_context():
        sub1 = SubscriptionService.create_subscription(user_a.id, {
            'company_name': 'Figma',
            'subscription_name': 'Professional',
            'account': 'figma_user',
            'end_date': '2026-12-31'
        })

    # User A exports JSON backup
    with client.session_transaction() as sess:
        sess['user_id'] = user_a.id

    res = client.get('/export/json')
    assert res.status_code == 200
    exported_data = json.loads(res.data)
    assert isinstance(exported_data, list)
    assert len(exported_data) == 1
    assert exported_data[0]['company_name'] == 'Figma'

    # Now User B attempts to import User A's exported JSON backup
    with client.session_transaction() as sess:
        sess['user_id'] = user_b.id

    # Add malicious user_id field in payload trying to hijack user_a
    exported_data[0]['user_id'] = user_a.id
    exported_data[0]['company_name'] = 'Figma (Imported by User B)'

    json_bytes = json.dumps(exported_data).encode('utf-8')
    data = {'file': (io.BytesIO(json_bytes), 'backup.json')}

    res_import = client.post('/import/json', data=data, content_type='multipart/form-data', follow_redirects=True)
    assert res_import.status_code == 200

    # Verify that the imported subscription belongs to User B and NOT User A
    with app.app_context():
        user_b_subs = Subscription.query.filter_by(user_id=user_b.id).all()
        assert len(user_b_subs) == 1
        assert user_b_subs[0].company_name == 'Figma (Imported by User B)'
        assert user_b_subs[0].user_id == user_b.id
