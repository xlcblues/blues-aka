from sqlalchemy import func

from blues_aka.extensions import db


class Permission(db.Model):
    __tablename__ = 'permissions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(100))
    description = db.Column(db.Text)
    resource = db.Column(db.String(50))  # 资源类型：user, role, permission等
    action = db.Column(db.String(50))  # 操作类型：create, read, update, delete等

    # 状态字段
    is_active = db.Column(db.String(20), default=True)

    # 时间戳
    created_at = db.Column(db.DateTime, default=func.now(), nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())