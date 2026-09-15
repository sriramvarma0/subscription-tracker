from app import db
from app.models.user import User

class UserService:
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
    def get_user_by_id(user_id: int) -> User:
        if not user_id:
            return None
        return db.session.get(User, int(user_id))
