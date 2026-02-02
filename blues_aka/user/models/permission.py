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
    deleted_at = db.Column(db.DateTime, nullable=True, index=True)  # 软删除时间戳

    is_deleted = db.Column(db.Boolean, default=False, index=True)

    def soft_delete(self):
        """
        软删除权限
        将权限标记为已删除,并记录删除时间
        """
        self.is_deleted = True
        self.deleted_at = func.now()
        # 注意: 不在这里 commit,由调用者负责事务管理

    def restore(self):
        """
        恢复已软删除的权限
        """
        self.is_deleted = False
        self.deleted_at = None
        # 注意: 不在这里 commit,由调用者负责事务管理

    @property
    def is_deleted_property(self):
        """
        检查权限是否已被软删除
        """
        return self.is_deleted or self.deleted_at is not None
