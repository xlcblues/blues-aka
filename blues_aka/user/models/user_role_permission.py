from sqlalchemy import func

from blues_aka.extensions import db


class user_roles(db.Model):
    """
    用户与角色的关联表（多对多关系）
    """
    __tablename__ = 'user_roles'

    # 外键关联到 users 表，设置级联删除
    # 作为复合主键的一部分，并为该列创建索引以提高查询性能
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        primary_key=True,
        index=True
    )

    # 外键关联到 roles 表，设置级联删除
    # 作为复合主键的一部分，并为该列创建索引以提高查询性能
    role_id = db.Column(
        db.Integer,
        db.ForeignKey('roles.id', ondelete='CASCADE'),
        primary_key=True,
        index=True
    )

    # 记录创建时间，默认为当前数据库时间
    created_at = db.Column(db.DateTime, default=func.now(), nullable=False)


class user_permissions(db.Model):
    """
    用户与权限的关联表（多对多关系）
    """
    __tablename__ = 'user_permissions'

    # 外键关联到 users 表，设置级联删除
    # 作为复合主键的一部分，并为该列创建索引以提高查询性能
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        primary_key=True,
        index=True
    )

    # 外键关联到 permissions 表，设置级联删除
    # 作为复合主键的一部分，并为该列创建索引以提高查询性能
    permission_id = db.Column(
        db.Integer,
        db.ForeignKey('permissions.id', ondelete='CASCADE'),
        primary_key=True,
        index=True
    )

    # 记录创建时间，默认为当前数据库时间
    created_at = db.Column(db.DateTime, default=func.now(), nullable=False)

