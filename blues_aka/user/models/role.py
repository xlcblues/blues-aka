from sqlalchemy import func

from blues_aka.extensions import db

class Role(db.Model):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    display_name = db.Column(db.String(100))
    description = db.Column(db.Text)

    # 状态字段
    is_active = db.Column(db.String(20), default=True)
    is_default = db.Column(db.String(20), default=False)

    # 时间戳
    created_at = db.Column(db.DateTime, default=func.now(), nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())