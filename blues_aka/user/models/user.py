from sqlalchemy import func
from sqlalchemy.dialects.postgresql import CITEXT
from werkzeug.security import check_password_hash, generate_password_hash

from blues_aka.extensions import db

class User(db.Model):
    __tablename__ = 'users'

    # 基础字段
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True, index=True)
    email = db.Column(CITEXT(), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    nickname = db.Column(db.String(100))
    phone = db.Column(db.String(20))

    # 状态字段
    status = db.Column(db.String(20), default='inactive', index=True)  # active, inactive, suspended, deleted
    is_verified = db.Column(db.Boolean, default=False, index=True)
    is_admin = db.Column(db.Boolean, default=False)

    # 登录相关
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime)
    last_login_at = db.Column(db.DateTime)
    last_login_ip = db.Column(db.String(45))
    login_count = db.Column(db.Integer, default=0)

    # 安全相关
    password_changed_at = db.Column(db.DateTime)
    email_verified_at = db.Column(db.DateTime)
    verification_token = db.Column(db.String(255))
    reset_password_token = db.Column(db.String(255))
    reset_password_expires = db.Column(db.DateTime)

    # 扩展信息
    profile = db.Column(db.JSON)  # 用户扩展信息
    preferences = db.Column(db.JSON)  # 用户偏好设置

    # 时间戳
    created_at = db.Column(db.DateTime, default=func.now(), nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())
    deleted_at = db.Column(db.DateTime, nullable=True, index=True)  # 软删除时间戳

    is_deleted = db.Column(db.Boolean, default=False, index=True)

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password) -> bool:
        if not User.is_strong_password(password):
            raise ValueError("密码强度不足！")
        self.password_hash = generate_password_hash(password)
        self.password_changed_at = func.now()
        return True

    def check_password(self, password) -> bool:
        return check_password_hash(self.password_hash, password)

    def soft_delete(self):
        """
        软删除用户
        将用户状态设置为deleted,并记录删除时间
        """
        self.status = 'deleted'
        self.deleted_at = func.now()

    def restore(self):
        """
        恢复已软删除的用户
        """
        self.status = 'active'
        self.deleted_at = None

    @property
    def is_deleted(self):
        """
        检查用户是否已被软删除
        """
        return self.status == 'deleted' or self.deleted_at is not None

    @staticmethod
    def is_strong_password(password) -> bool:
        if password is None:
            return False
        elif len(password) < 8:
            return False
        has_letter = any(c.isalpha() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)

        conditions_met = sum([has_letter, has_digit, has_special])

        if conditions_met < 2:
            return False

        return True
