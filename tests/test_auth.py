import pytest
from app import db
from app.models.user import User
from app.services.user_service import UserService

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

def test_signup_and_login_flow(client, app):
    # GET login page
    res = client.get('/login')
    assert res.status_code == 200
    assert b"Subscription Tracker" in res.data

    # Sign Up new user
    res_signup = client.post('/signup', data={
        'action': 'signup',
        'email': '  New.User@Example.Com  ',
        'password': 'SecurePassword123',
        'confirm_password': 'SecurePassword123'
    }, follow_redirects=True)
    assert res_signup.status_code == 200
    assert b"new.user@example.com" in res_signup.data

    with client.session_transaction() as sess:
        user_id = sess.get('user_id')
        assert user_id is not None

    with app.app_context():
        user = db.session.get(User, user_id)
        assert user is not None
        assert user.email == "new.user@example.com"
        assert user.check_password("SecurePassword123") is True

    # Logout
    res_logout = client.get('/logout', follow_redirects=True)
    assert res_logout.status_code == 200
    with client.session_transaction() as sess:
        assert 'user_id' not in sess

    # Attempt Login with WRONG password
    res_wrong = client.post('/login', data={
        'action': 'login',
        'email': 'new.user@example.com',
        'password': 'WrongPassword'
    })
    assert res_wrong.status_code == 400
    assert b"Invalid email or password" in res_wrong.data

    # Login with CORRECT password
    res_login = client.post('/login', data={
        'action': 'login',
        'email': 'new.user@example.com',
        'password': 'SecurePassword123'
    }, follow_redirects=True)
    assert res_login.status_code == 200
    assert b"new.user@example.com" in res_login.data

def test_legacy_user_password_upgrade_flow(client, app):
    # Create legacy user in database without password
    with app.app_context():
        legacy_user = User(email="legacy.user@example.com")
        db.session.add(legacy_user)
        db.session.commit()
        legacy_user_id = legacy_user.id
        assert legacy_user.has_password is False

    # Legacy user attempts login with email
    res = client.post('/login', data={
        'action': 'login',
        'email': 'legacy.user@example.com'
    })
    assert res.status_code == 200
    assert b"set a password to upgrade your account security" in res.data

    # Legacy user sets new password
    res_set = client.post('/login', data={
        'action': 'set_password',
        'user_id': str(legacy_user_id),
        'email': 'legacy.user@example.com',
        'password': 'MyNewSecretPassword',
        'confirm_password': 'MyNewSecretPassword'
    }, follow_redirects=True)
    assert res_set.status_code == 200
    assert b"legacy.user@example.com" in res_set.data

    with app.app_context():
        updated_user = db.session.get(User, legacy_user_id)
        assert updated_user.has_password is True
        assert updated_user.check_password("MyNewSecretPassword") is True

def test_signup_validation_errors(client, app):
    # Short password
    res1 = client.post('/signup', data={
        'action': 'signup', 'email': 'user1@example.com', 'password': '123', 'confirm_password': '123'
    })
    assert res1.status_code == 400
    assert b"Password must be at least 6 characters long" in res1.data

    # Mismatch password
    res2 = client.post('/signup', data={
        'action': 'signup', 'email': 'user2@example.com', 'password': 'Password123', 'confirm_password': 'Password456'
    })
    assert res2.status_code == 400
    assert b"Passwords do not match" in res2.data

    # Duplicate email
    with app.app_context():
        UserService.register_user('existing@example.com', 'Password123', 'Password123')

    res3 = client.post('/signup', data={
        'action': 'signup', 'email': 'existing@example.com', 'password': 'Password123', 'confirm_password': 'Password123'
    })
    assert res3.status_code == 400
    assert b"An account with this email already exists" in res3.data

def test_health_endpoint(client):
    res = client.get('/health')
    assert res.status_code == 200
    assert res.get_json() == {'status': 'healthy'}
