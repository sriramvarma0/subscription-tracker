from app import db
from app.models.user import User

class UserService:
    @staticmethod
    def get_by_email(email: str) -> User:
        normalized_email = User.normalize_email(email)
        if not normalized_email:
            return None
        return User.query.filter_by(email=normalized_email).first()

    @staticmethod
    def get_or_create_user(email: str) -> User:
        normalized_email = User.normalize_email(email)
        if not User.validate_email(normalized_email):
            raise ValueError("Invalid email format.")

        user = User.query.filter_by(email=normalized_email).first()
        if not user:
            user = User(email=normalized_email)
            db.session.add(user)
            db.session.commit()
        return user

    @staticmethod
    def register_user(email: str, password: str, confirm_password: str) -> User:
        normalized_email = User.normalize_email(email)
        if not User.validate_email(normalized_email):
            raise ValueError("Invalid email format.")

        existing = User.query.filter_by(email=normalized_email).first()
        if existing:
            raise ValueError("An account with this email already exists. Please log in.")

        password = password or ''
        confirm_password = confirm_password or ''

        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters long.")

        if password != confirm_password:
            raise ValueError("Passwords do not match.")

        user = User(email=normalized_email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def authenticate_user(email: str, password: str = None):
        normalized_email = User.normalize_email(email)
        if not User.validate_email(normalized_email):
            raise ValueError("Invalid email format.")

        user = User.query.filter_by(email=normalized_email).first()
        if not user:
            raise ValueError("No account found with this email. Please sign up.")

        if not user.has_password:
            return ('NEEDS_PASSWORD_SET', user)

        if not password:
            raise ValueError("Password is required.")

        if not user.check_password(password):
            raise ValueError("Invalid email or password.")

        return ('SUCCESS', user)

    @staticmethod
    def set_user_password(user: User, password: str, confirm_password: str) -> User:
        password = password or ''
        confirm_password = confirm_password or ''

        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters long.")

        if password != confirm_password:
            raise ValueError("Passwords do not match.")

        user.set_password(password)
        db.session.commit()
        return user

    @staticmethod
    def get_user_by_id(user_id: int) -> User:
        if not user_id:
            return None
        return db.session.get(User, int(user_id))
