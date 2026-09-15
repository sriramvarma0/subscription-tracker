import pytest
from app import db
from app.models.user import User

def test_email_normalization():
    assert User.normalize_email("  TEST.User@Example.COM  ") == "test.user@example.com"
    assert User.normalize_email("USER@DOMAIN.ORG") == "user@domain.org"
    assert User.normalize_email("") == ""

def test_email_validation():
    assert User.validate_email("user@example.com") is True
    assert User.validate_email("invalid-email") is False
    assert User.validate_email("@missinglocal.com") is False
    assert User.validate_email("missingdomain@.com") is False
    assert User.validate_email("") is False

def test_login_flow(client, app):
    # GET login page
    res = client.get('/login')
    assert res.status_code == 200
    assert b"Subscription Tracker" in res.data

    # Submit valid email -> Creates user and sets session
    res = client.post('/login', data={'email': '  New.User@Example.Com  '}, follow_redirects=True)
    assert res.status_code == 200
    assert b"new.user@example.com" in res.data

    with client.session_transaction() as sess:
        user_id = sess.get('user_id')
        assert user_id is not None

    with app.app_context():
        user = db.session.get(User, user_id)
        assert user is not None
        assert user.email == "new.user@example.com"

    # Logout
    res = client.get('/logout', follow_redirects=True)
    assert res.status_code == 200
    with client.session_transaction() as sess:
        assert 'user_id' not in sess

def test_invalid_email_login_rejection(client):
    res = client.post('/login', data={'email': 'not-an-email'})
    assert res.status_code == 400
    assert b"Invalid email format" in res.data

def test_health_endpoint(client):
    res = client.get('/health')
    assert res.status_code == 200
    assert res.get_json() == {'status': 'healthy'}
