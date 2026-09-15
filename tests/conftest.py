import pytest
from app import create_app, db
from config import TestingConfig
from app.models.user import User
from app.models.subscription import Subscription

@pytest.fixture
def app():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def user_a(app):
    with app.app_context():
        user = User(email="user.a@example.com")
        db.session.add(user)
        db.session.commit()
        return db.session.get(User, user.id)

@pytest.fixture
def user_b(app):
    with app.app_context():
        user = User(email="user.b@example.com")
        db.session.add(user)
        db.session.commit()
        return db.session.get(User, user.id)
