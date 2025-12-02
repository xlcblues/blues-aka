from sqlalchemy import func, text
from sqlalchemy.dialects.postgresql import CITEXT
from werkzeug.security import generate_password_hash, check_password_hash
from blues_aka.extensions import db

class User(db.Model):
    __tablename__ = 'users'
    # 主键字段 (自动递增)
    id = db.Column(
        db.BigInteger,
        primary_key=True,
        autoincrement=True,
        server_default=db.text("nextval('users_id_seq'::regclass)")
    )

    # 用户名 (唯一)
    username = db.Column(
        db.String(50),
        nullable=False,
        unique=True
    )

    # 邮箱 (不区分大小写的唯一)
    email = db.Column(
        CITEXT(),
        nullable=False,
        unique=True
    )

    # 密码哈希
    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    # 昵称 (可选)
    nickname = db.Column(
        db.String(100)
    )

    # 用户状态 (带检查约束)
    status = db.Column(
        db.String(20),
        nullable=False,
        default='inactive',
        server_default='inactive',
        info={'check': "status IN ('active', 'inactive', 'suspended', 'deleted')"}
    )

    # 验证状态
    is_verified = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        server_default='false'
    )

    # 时间戳字段
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    last_login_at = db.Column(
        db.DateTime(timezone=True)
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # 设置 updated_at 触发器
    @staticmethod
    def create_updated_at_trigger():
        """创建自动更新 updated_at 字段的触发器"""
        db.session.execute(text('''
                CREATE OR REPLACE FUNCTION public.trigger_set_timestamp()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = now();
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
            '''))

        db.session.execute(text('''
                CREATE TRIGGER set_timestamp
                BEFORE UPDATE ON public.users
                FOR EACH ROW
                EXECUTE PROCEDURE public.trigger_set_timestamp();
            '''))
        db.session.commit()

    def __repr__(self):
        return f'<User {self.username}>'